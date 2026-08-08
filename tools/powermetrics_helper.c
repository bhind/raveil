#include <errno.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

#define HELPER_VERSION "raveil-powermetrics-helper/v1"
#define EX_USAGE 64
#define EX_NOPERM 77
#define EX_OSERR 71

static int parse_integer(const char *text, long *value) {
    char *end = NULL;
    errno = 0;
    long parsed = strtol(text, &end, 10);
    if (errno != 0 || end == text || *end != '\0') {
        return 0;
    }
    *value = parsed;
    return 1;
}

int main(int argc, char **argv) {
    if (argc == 2 && strcmp(argv[1], "--version") == 0) {
        puts(HELPER_VERSION);
        return 0;
    }
    if (argc != 5 || strcmp(argv[1], "--sample-rate") != 0 ||
        strcmp(argv[3], "--sample-count") != 0) {
        fputs("usage: raveil-powermetrics --sample-rate 20..1000 "
              "--sample-count 1|-1\n", stderr);
        return EX_USAGE;
    }
    long sample_rate = 0;
    long sample_count = 0;
    if (!parse_integer(argv[2], &sample_rate) || sample_rate < 20 ||
        sample_rate > 1000 || !parse_integer(argv[4], &sample_count) ||
        (sample_count != 1 && sample_count != -1)) {
        fputs("raveil-powermetrics rejected arguments\n", stderr);
        return EX_USAGE;
    }
    if (geteuid() != 0) {
        fputs("raveil-powermetrics must be invoked through authorized sudo\n", stderr);
        return EX_NOPERM;
    }

    char *const command[] = {
        "/usr/bin/powermetrics",
        "--samplers",
        "cpu_power,thermal",
        "--sample-rate",
        argv[2],
        "--sample-count",
        argv[4],
        "--format",
        "text",
        "--buffer-size",
        "1",
        "--handle-invalid-values",
        NULL,
    };
    char *const environment[] = {"LC_ALL=C", NULL};
    execve(command[0], command, environment);
    fprintf(stderr, "raveil-powermetrics execve failed: %s\n", strerror(errno));
    return EX_OSERR;
}
