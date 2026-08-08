#include <errno.h>
#include <inttypes.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

static volatile uint64_t checksum_sink;

typedef struct {
    const char *family;
    size_t m;
    size_t n;
    size_t k;
    const char *loop_order;
    size_t tile;
    const char *materialization;
    size_t warmups;
    size_t iterations;
} options_t;

static int checked_count(size_t a, size_t b, size_t *result) {
    if (a != 0 && b > SIZE_MAX / a) {
        return 0;
    }
    *result = a * b;
    return 1;
}

static int64_t *alloc_i64(size_t count) {
    if (count > SIZE_MAX / sizeof(int64_t)) {
        return NULL;
    }
    return calloc(count, sizeof(int64_t));
}

static int32_t *alloc_i32(size_t count) {
    if (count > SIZE_MAX / sizeof(int32_t)) {
        return NULL;
    }
    return calloc(count, sizeof(int32_t));
}

static void fill_i32(int32_t *values, size_t count, uint32_t salt) {
    uint32_t state = UINT32_C(0x9e3779b9) ^ salt;
    for (size_t index = 0; index < count; ++index) {
        state = state * UINT32_C(1664525) + UINT32_C(1013904223);
        values[index] = (int32_t)((state >> 16) % 7) - 3;
    }
}

static uint64_t checksum(const int64_t *values, size_t count) {
    uint64_t hash = UINT64_C(1469598103934665603);
    for (size_t index = 0; index < count; ++index) {
        uint64_t word = (uint64_t)values[index];
        for (unsigned shift = 0; shift < 64; shift += 8) {
            hash ^= (word >> shift) & UINT64_C(0xff);
            hash *= UINT64_C(1099511628211);
        }
    }
    return hash;
}

static uint64_t elapsed_ns(struct timespec start, struct timespec end) {
    uint64_t seconds = (uint64_t)(end.tv_sec - start.tv_sec);
    int64_t nanos = end.tv_nsec - start.tv_nsec;
    if (nanos < 0) {
        --seconds;
        nanos += INT64_C(1000000000);
    }
    return seconds * UINT64_C(1000000000) + (uint64_t)nanos;
}

static void gemm_reference(const int32_t *a, const int32_t *b, int64_t *c,
                           size_t m, size_t n, size_t k) {
    memset(c, 0, m * n * sizeof(*c));
    for (size_t i = 0; i < m; ++i) {
        for (size_t j = 0; j < n; ++j) {
            int64_t sum = 0;
            for (size_t p = 0; p < k; ++p) {
                sum += (int64_t)a[i * k + p] * (int64_t)b[p * n + j];
            }
            c[i * n + j] = sum;
        }
    }
}

static void gemm_ikj(const int32_t *a, const int32_t *b, int64_t *c,
                     size_t m, size_t n, size_t k) {
    memset(c, 0, m * n * sizeof(*c));
    for (size_t i = 0; i < m; ++i) {
        for (size_t p = 0; p < k; ++p) {
            int64_t av = a[i * k + p];
            for (size_t j = 0; j < n; ++j) {
                c[i * n + j] += av * (int64_t)b[p * n + j];
            }
        }
    }
}

static size_t minimum(size_t left, size_t right) {
    return left < right ? left : right;
}

static void gemm_tiled(const int32_t *a, const int32_t *b, int64_t *c,
                       size_t m, size_t n, size_t k, size_t tile) {
    memset(c, 0, m * n * sizeof(*c));
    for (size_t ii = 0; ii < m; ii += tile) {
        for (size_t pp = 0; pp < k; pp += tile) {
            for (size_t jj = 0; jj < n; jj += tile) {
                for (size_t i = ii; i < minimum(ii + tile, m); ++i) {
                    for (size_t p = pp; p < minimum(pp + tile, k); ++p) {
                        int64_t av = a[i * k + p];
                        for (size_t j = jj; j < minimum(jj + tile, n); ++j) {
                            c[i * n + j] += av * (int64_t)b[p * n + j];
                        }
                    }
                }
            }
        }
    }
}

static void gemm_candidate(const options_t *options, const int32_t *a,
                           const int32_t *b, int64_t *c) {
    if (strcmp(options->loop_order, "ijk") == 0) {
        gemm_reference(a, b, c, options->m, options->n, options->k);
    } else if (strcmp(options->loop_order, "ikj") == 0) {
        gemm_ikj(a, b, c, options->m, options->n, options->k);
    } else {
        gemm_tiled(a, b, c, options->m, options->n, options->k, options->tile);
    }
}

static void bias_relu(int64_t *values, const int64_t *bias, size_t m, size_t n) {
    for (size_t i = 0; i < m; ++i) {
        for (size_t j = 0; j < n; ++j) {
            int64_t value = values[i * n + j] + bias[j];
            values[i * n + j] = value > 0 ? value : 0;
        }
    }
}

static void gemm_bias_relu_fused(const options_t *options, const int32_t *a,
                                 const int32_t *b, const int64_t *bias,
                                 int64_t *output) {
    for (size_t i = 0; i < options->m; ++i) {
        for (size_t j = 0; j < options->n; ++j) {
            int64_t sum = 0;
            size_t step = strcmp(options->loop_order, "tiled") == 0 ? options->tile : options->k;
            for (size_t pp = 0; pp < options->k; pp += step) {
                for (size_t p = pp; p < minimum(pp + step, options->k); ++p) {
                    sum += (int64_t)a[i * options->k + p] * (int64_t)b[p * options->n + j];
                }
            }
            sum += bias[j];
            output[i * options->n + j] = sum > 0 ? sum : 0;
        }
    }
}

static void gemm_i64_i32(const int64_t *a, const int32_t *b, int64_t *c,
                         size_t m, size_t n, size_t k, const options_t *options) {
    memset(c, 0, m * n * sizeof(*c));
    if (strcmp(options->loop_order, "ijk") == 0) {
        for (size_t i = 0; i < m; ++i) {
            for (size_t j = 0; j < n; ++j) {
                int64_t sum = 0;
                for (size_t p = 0; p < k; ++p) {
                    sum += a[i * k + p] * (int64_t)b[p * n + j];
                }
                c[i * n + j] = sum;
            }
        }
        return;
    }
    size_t tile = strcmp(options->loop_order, "tiled") == 0 ? options->tile : k;
    for (size_t pp = 0; pp < k; pp += tile) {
        for (size_t i = 0; i < m; ++i) {
            for (size_t p = pp; p < minimum(pp + tile, k); ++p) {
                int64_t av = a[i * k + p];
                for (size_t j = 0; j < n; ++j) {
                    c[i * n + j] += av * (int64_t)b[p * n + j];
                }
            }
        }
    }
}

static void execute(const options_t *options, const int32_t *a, const int32_t *b,
                    const int32_t *b2, const int64_t *bias, int64_t *scratch,
                    int64_t *output) {
    if (strcmp(options->family, "gemm") == 0) {
        gemm_candidate(options, a, b, output);
        return;
    }
    if (strcmp(options->materialization, "fused") == 0) {
        gemm_bias_relu_fused(options, a, b, bias, output);
    } else {
        gemm_candidate(options, a, b, output);
        bias_relu(output, bias, options->m, options->n);
    }
    if (strcmp(options->family, "gemm_bias_relu") == 0) {
        return;
    }
    memcpy(scratch, output, options->m * options->n * sizeof(*scratch));
    gemm_i64_i32(scratch, b2, output, options->m, options->k, options->n, options);
}

static int parse_size(const char *text, size_t *value) {
    char *end = NULL;
    errno = 0;
    unsigned long long parsed = strtoull(text, &end, 10);
    if (errno != 0 || end == text || *end != '\0' || parsed == 0 || parsed > 512) {
        return 0;
    }
    *value = (size_t)parsed;
    return 1;
}

static int parse_options(int argc, char **argv, options_t *options) {
    if (argc != 10) {
        return 0;
    }
    options->family = argv[1];
    options->loop_order = argv[5];
    options->materialization = argv[7];
    if (!parse_size(argv[2], &options->m) || !parse_size(argv[3], &options->n) ||
        !parse_size(argv[4], &options->k) || !parse_size(argv[8], &options->warmups) ||
        !parse_size(argv[9], &options->iterations)) {
        return 0;
    }
    if (strcmp(argv[6], "0") == 0) {
        options->tile = 0;
    } else if (!parse_size(argv[6], &options->tile)) {
        return 0;
    }
    int family_ok = strcmp(options->family, "gemm") == 0 ||
                    strcmp(options->family, "gemm_bias_relu") == 0 ||
                    strcmp(options->family, "mlp2") == 0;
    int loop_ok = strcmp(options->loop_order, "ijk") == 0 ||
                  strcmp(options->loop_order, "ikj") == 0 ||
                  strcmp(options->loop_order, "tiled") == 0;
    int materialization_ok = strcmp(options->materialization, "fused") == 0 ||
                             strcmp(options->materialization, "materialized") == 0;
    return family_ok && loop_ok && materialization_ok &&
           ((strcmp(options->loop_order, "tiled") == 0) == (options->tile != 0));
}

int main(int argc, char **argv) {
    options_t options;
    if (!parse_options(argc, argv, &options)) {
        fputs("invalid arguments\n", stderr);
        return 2;
    }

    size_t a_count = 0;
    size_t b_count = 0;
    size_t out_count = 0;
    size_t hidden_count = 0;
    if (!checked_count(options.m, options.k, &a_count) ||
        !checked_count(options.k, options.n, &b_count) ||
        !checked_count(options.m, options.n, &hidden_count)) {
        fputs("dimension overflow\n", stderr);
        return 2;
    }
    out_count = strcmp(options.family, "mlp2") == 0 ? a_count : hidden_count;

    int32_t *a = alloc_i32(a_count);
    int32_t *b = alloc_i32(b_count);
    int32_t *b2 = alloc_i32(options.n * options.k);
    int64_t *bias = alloc_i64(options.n);
    int64_t *scratch = alloc_i64(hidden_count);
    int64_t *output = alloc_i64(hidden_count > out_count ? hidden_count : out_count);
    int64_t *reference = alloc_i64(hidden_count > out_count ? hidden_count : out_count);
    if (!a || !b || !b2 || !bias || !scratch || !output || !reference) {
        fputs("allocation failed\n", stderr);
        return 2;
    }
    fill_i32(a, a_count, 1);
    fill_i32(b, b_count, 2);
    fill_i32(b2, options.n * options.k, 3);
    for (size_t j = 0; j < options.n; ++j) {
        bias[j] = (int64_t)(j % 11) - 5;
    }

    options_t reference_options = options;
    reference_options.loop_order = "ijk";
    reference_options.tile = 0;
    reference_options.materialization = "materialized";
    execute(&reference_options, a, b, b2, bias, scratch, reference);
    uint64_t expected = checksum(reference, out_count);

    for (size_t index = 0; index < options.warmups; ++index) {
        execute(&options, a, b, b2, bias, scratch, output);
        checksum_sink ^= checksum(output, out_count);
    }
    struct timespec start;
    struct timespec end;
    if (clock_gettime(CLOCK_MONOTONIC, &start) != 0) {
        return 2;
    }
    for (size_t index = 0; index < options.iterations; ++index) {
        execute(&options, a, b, b2, bias, scratch, output);
        checksum_sink ^= (uint64_t)output[index % out_count];
    }
    if (clock_gettime(CLOCK_MONOTONIC, &end) != 0) {
        return 2;
    }
    uint64_t actual = checksum(output, out_count);
    uint64_t latency = elapsed_ns(start, end) / options.iterations;
    if (latency == 0) {
        latency = 1;
    }
    int valid = actual == expected;
    printf("{\"latency_ns\":%" PRIu64 ",\"checksum\":\"%016" PRIx64
           "\",\"reference_checksum\":\"%016" PRIx64
           "\",\"semantic_valid\":%s,\"failure\":\"%s\"}\n",
           latency, actual, expected, valid ? "true" : "false",
           valid ? "" : "checksum mismatch");

    free(a);
    free(b);
    free(b2);
    free(bias);
    free(scratch);
    free(output);
    free(reference);
    return valid ? 0 : 3;
}
