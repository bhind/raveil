#include "graph_device_dag_runtime.h"

#include "graph_device_abi_generated.h"
#include "graph_device_affine_generated.h"
#include "graph_device_dag_generated.h"

#include <array>
#include <cerrno>
#include <cstdint>
#include <fcntl.h>
#include <fstream>
#include <iostream>
#include <string>
#include <unistd.h>

namespace raveil::graph_device {
namespace {

namespace generated = dag_generated;
namespace affine_generated = raveil::graph_device::affine_generated;
using Input = std::array<std::uint32_t, abi::kInputCount>;
using Output = std::array<std::uint32_t, abi::kOutputCount>;
using Payload = std::array<std::uint32_t, program_abi::kPayloadCount>;

template <std::size_t Count>
bool load_words(
    const std::filesystem::path& path,
    std::array<std::uint32_t, Count>& words
) {
    std::ifstream stream(path, std::ios::binary);
    if (!stream) return false;
    std::array<unsigned char, Count * 4U> bytes{};
    stream.read(reinterpret_cast<char*>(bytes.data()), bytes.size());
    if (stream.gcount() != static_cast<std::streamsize>(bytes.size())
        || stream.peek() != EOF) return false;
    for (std::size_t index = 0; index < Count; ++index) {
        const unsigned char* p = bytes.data() + index * 4U;
        words[index] = static_cast<std::uint32_t>(p[0])
            | (static_cast<std::uint32_t>(p[1]) << 8U)
            | (static_cast<std::uint32_t>(p[2]) << 16U)
            | (static_cast<std::uint32_t>(p[3]) << 24U);
    }
    return true;
}

bool store_output(const std::filesystem::path& path, const Output& words) {
    int flags = O_WRONLY | O_CREAT | O_EXCL;
#ifdef O_CLOEXEC
    flags |= O_CLOEXEC;
#endif
#ifdef O_NOFOLLOW
    flags |= O_NOFOLLOW;
#endif
    const int descriptor = ::open(path.c_str(), flags, 0600);
    if (descriptor < 0) return false;
    for (const std::uint32_t word : words) {
        const std::array<unsigned char, 4> bytes = {
            static_cast<unsigned char>(word),
            static_cast<unsigned char>(word >> 8U),
            static_cast<unsigned char>(word >> 16U),
            static_cast<unsigned char>(word >> 24U),
        };
        std::size_t written = 0;
        while (written < bytes.size()) {
            const ssize_t result = ::write(
                descriptor, bytes.data() + written, bytes.size() - written
            );
            if (result < 0 && errno == EINTR) continue;
            if (result <= 0) {
                ::close(descriptor);
                return false;
            }
            written += static_cast<std::size_t>(result);
        }
    }
    return ::close(descriptor) == 0;
}

bool read_device(DeviceTransport& device, std::uint32_t offset, std::uint32_t& value) {
    const DeviceRead result = device.read_word(offset);
    if (!result.ok) return false;
    value = result.value;
    return true;
}

bool read_program(
    ProgramInstallTransport& installer,
    std::uint32_t offset,
    std::uint32_t& value
) {
    const DeviceRead result = installer.read_program_word(offset);
    if (!result.ok) return false;
    value = result.value;
    return true;
}

bool reset(DeviceTransport& device, std::ostream& errors) {
    if (!device.write_word(abi::kRegControl, abi::kControlReset)) {
        errors << "DAG reset failed\n";
        return false;
    }
    return true;
}

bool install_affine(
    AffineInstallTransport& installer,
    const affine_generated::Profile& profile,
    std::ostream& errors
) {
    if (!installer.write_install_word(install_abi::kRegControl,
            install_abi::kControlClear)) return false;
    for (std::uint32_t index = 0; index < profile.payload.size(); ++index) {
        if (!installer.write_install_word(install_abi::kPayloadBase + index,
                profile.payload[index])) {
            errors << "DAG affine payload failed word=" << index << '\n';
            return false;
        }
    }
    if (!installer.write_install_word(install_abi::kRegControl,
            install_abi::kControlCommit)) return false;
    const DeviceRead status = installer.read_install_word(install_abi::kRegStatus);
    return status.ok && (status.value & install_abi::kStatusInstalled) != 0U
        && (status.value & install_abi::kStatusFault) == 0U;
}

bool install_program(
    ProgramInstallTransport& installer,
    const generated::Graph& graph,
    std::ostream& errors
) {
    if (!installer.write_program_word(program_abi::kRegControl,
            program_abi::kControlClear)) return false;
    std::uint32_t count = 0U;
    for (std::uint32_t index = 0; index < graph.payload.size(); ++index) {
        if (!installer.write_program_word(program_abi::kPayloadBase + index,
                graph.payload[index])
            || !read_program(installer, program_abi::kRegPayloadCount, count)
            || count != index + 1U) {
            errors << "DAG program payload failed graph=" << graph.id
                   << " word=" << index << '\n';
            return false;
        }
    }
    if (!installer.write_program_word(program_abi::kRegControl,
            program_abi::kControlCommit)) return false;
    std::uint32_t status = 0U;
    if (!read_program(installer, program_abi::kRegStatus, status)
        || (status & program_abi::kStatusInstalled) == 0U
        || (status & (program_abi::kStatusLoading | program_abi::kStatusFault)) != 0U) {
        errors << "DAG program commit failed graph=" << graph.id << '\n';
        return false;
    }
    for (std::uint32_t index = 0; index < 8U; ++index) {
        std::uint32_t digest = 0U;
        if (!read_program(installer, program_abi::kRegDigestBase + index, digest)
            || digest != graph.payload[4U + index]) {
            errors << "DAG live digest mismatch graph=" << graph.id << '\n';
            return false;
        }
    }
    return true;
}

bool stage_and_start(DeviceTransport& device, const Input& input, std::ostream& errors) {
    for (std::uint32_t index = 0; index < input.size(); ++index) {
        if (!device.write_word(abi::kInputBase + index, input[index])) {
            errors << "DAG staging failed word=" << index << '\n';
            return false;
        }
    }
    if (!device.write_word(abi::kRegControl, abi::kControlStart)) {
        errors << "DAG start failed\n";
        return false;
    }
    return true;
}

bool wait_terminal(
    DeviceTransport& device,
    std::uint32_t& polls,
    std::uint32_t& status,
    std::ostream& errors
) {
    for (polls = 1U; polls <= abi::kMaxStatusPolls; ++polls) {
        if (!read_device(device, abi::kRegStatus, status)) return false;
        if ((status & abi::kStatusFault) != 0U) {
            errors << "DAG device faulted\n";
            return false;
        }
        if ((status & (abi::kStatusCompleted | abi::kStatusCancelled)) != 0U) return true;
    }
    errors << "DAG finite timeout exceeded\n";
    return false;
}

bool read_output(DeviceTransport& device, Output& output, std::ostream& errors) {
    for (std::uint32_t index = 0; index < output.size(); ++index) {
        const DeviceRead result = device.read_word(abi::kOutputBase + index);
        if (!result.ok) {
            errors << "DAG private output failed word=" << index << '\n';
            return false;
        }
        output[index] = result.value;
    }
    return true;
}

bool valid_fallback_program(const Payload& payload) {
    if (payload[0] != 0x52504731U
        || (payload[1] != 1U && payload[1] != 2U && payload[1] != 3U && payload[1] != 4U)
        || payload[2] < 2U || payload[2] > 16U || payload[3] != 8U) return false;
    std::array<bool, 8> defined{};
    unsigned stores = 0U;
    for (std::size_t index = 0; index < 16U; ++index) {
        const std::uint32_t instruction = payload[12U + index];
        const bool active = index < payload[2];
        if (!active) { if (instruction != 0U) return false; continue; }
        const std::uint32_t opcode = instruction >> 28U;
        const std::uint32_t destination = (instruction >> 25U) & 7U;
        const std::uint32_t left = (instruction >> 22U) & 7U;
        const std::uint32_t right = (instruction >> 19U) & 7U;
        const std::uint32_t row_bits = (instruction >> 20U) & 31U;
        const std::uint32_t column_bits = (instruction >> 15U) & 31U;
        const bool signed_unit_row = row_bits == 0U || row_bits == 1U
            || row_bits == 31U;
        const bool signed_unit_column = column_bits == 0U
            || column_bits == 1U || column_bits == 31U;
        const bool legacy_load = payload[1] != 3U && payload[1] != 4U && left <= 4U
            && (instruction & 0x003fffffU) == 0U;
        const bool relative_load = (payload[1] == 3U || payload[1] == 4U) && signed_unit_row
            && signed_unit_column && (instruction & 0x00007fffU) == 0U;
        const bool load = opcode == 1U && index + 1U < payload[2]
            && (legacy_load || relative_load);
        const bool add = opcode == 2U && index + 1U < payload[2]
            && (instruction & 0x0007ffffU) == 0U && defined[left] && defined[right];
        const bool max_u32 = opcode == 4U
            && (payload[1] == 2U || payload[1] == 3U || payload[1] == 4U)
            && index + 1U < payload[2]
            && (instruction & 0x0007ffffU) == 0U && defined[left] && defined[right];
        const bool mul_u32 = opcode == 5U && payload[1] == 4U
            && index + 1U < payload[2]
            && (instruction & 0x0007ffffU) == 0U && defined[left] && defined[right];
        const bool store = opcode == 3U && index + 1U == payload[2]
            && (instruction & 0x01ffffffU) == 0U && defined[destination];
        if (!(load || add || max_u32 || mul_u32 || store)) return false;
        if (load || add || max_u32 || mul_u32) defined[destination] = true;
        if (store) ++stores;
    }
    for (std::size_t index = 28U; index < payload.size(); ++index)
        if (payload[index] != 0U) return false;
    return stores == 1U;
}

bool fallback(
    const generated::Graph& graph,
    const affine_generated::Profile& affine,
    const Input& input,
    Output& output
) {
    if (!valid_fallback_program(graph.payload)) return false;
    output.fill(0U);
    const std::uint32_t rows = affine.payload[2];
    const std::uint32_t columns = affine.payload[3];
    const std::uint32_t input_stride = affine.payload[4];
    const std::uint32_t output_stride = affine.payload[5];
    for (std::uint32_t row = 0; row < rows; ++row) {
        for (std::uint32_t column = 0; column < columns; ++column) {
            std::array<std::uint32_t, 8> values{};
            const std::uint32_t center = (row + 1U) * input_stride + column + 1U;
            for (std::uint32_t pc = 0; pc < graph.payload[2]; ++pc) {
                const std::uint32_t instruction = graph.payload[12U + pc];
                const std::uint32_t opcode = instruction >> 28U;
                const std::uint32_t destination = (instruction >> 25U) & 7U;
                if (opcode == 1U) {
                    std::uint32_t address = center;
                    if (graph.payload[1] == 3U || graph.payload[1] == 4U) {
                        const auto signed_five = [](std::uint32_t value) {
                            return (value & 16U) != 0U
                                ? static_cast<std::int32_t>(value) - 32
                                : static_cast<std::int32_t>(value);
                        };
                        const std::int32_t row_delta = signed_five(
                            (instruction >> 20U) & 31U);
                        const std::int32_t column_delta = signed_five(
                            (instruction >> 15U) & 31U);
                        const std::int32_t relative = static_cast<std::int32_t>(center)
                            + row_delta * static_cast<std::int32_t>(input_stride)
                            + column_delta;
                        if (relative < 0 || relative >= 324) return false;
                        address = static_cast<std::uint32_t>(relative);
                    } else {
                        const std::uint32_t selector = (instruction >> 22U) & 7U;
                        if (selector == 1U) address -= input_stride;
                        else if (selector == 2U) address += input_stride;
                        else if (selector == 3U) address -= 1U;
                        else if (selector == 4U) address += 1U;
                        else if (selector != 0U) return false;
                    }
                    values[destination] = input[address];
                } else if (opcode == 2U) {
                    values[destination] = values[(instruction >> 22U) & 7U]
                        + values[(instruction >> 19U) & 7U];
                } else if (opcode == 4U) {
                    const auto left = values[(instruction >> 22U) & 7U];
                    const auto right = values[(instruction >> 19U) & 7U];
                    values[destination] = left >= right ? left : right;
                } else if (opcode == 5U) {
                    values[destination] = values[(instruction >> 22U) & 7U]
                        * values[(instruction >> 19U) & 7U];
                } else if (opcode == 3U) {
                    output[row * output_stride + column] = values[destination];
                } else return false;
            }
        }
    }
    return true;
}

bool expect_fault(ProgramInstallTransport& installer) {
    std::uint32_t status = 0U;
    return read_program(installer, program_abi::kRegStatus, status)
        && (status & program_abi::kStatusFault) != 0U
        && (status & program_abi::kStatusInstalled) == 0U;
}

bool malformed_case(
    DeviceTransport& device,
    ProgramInstallTransport& installer,
    Payload payload,
    unsigned kind
) {
    if (!reset(device, std::cerr)
        || !installer.write_program_word(program_abi::kRegControl,
            program_abi::kControlClear)) return false;
    if (kind == 0U) {
        installer.write_program_word(program_abi::kPayloadBase, payload[0]);
        installer.write_program_word(program_abi::kRegControl, program_abi::kControlCommit);
        return expect_fault(installer);
    }
    if (kind == 1U) {
        installer.write_program_word(program_abi::kPayloadBase + 1U, payload[1]);
        return expect_fault(installer);
    }
    if (kind == 2U) {
        installer.write_program_word(program_abi::kPayloadBase, payload[0]);
        installer.write_program_word(program_abi::kPayloadBase, payload[0]);
        return expect_fault(installer);
    }
    if (kind == 3U) payload[12] = 0xf0000000U;
    if (kind == 4U) payload[12] = 0x20080000U;
    if (kind == 5U) payload[28] = 1U;
    if (kind == 6U) payload[12U + payload[2] - 1U] = 0x10000000U;
    for (std::uint32_t index = 0; index < payload.size(); ++index) {
        installer.write_program_word(program_abi::kPayloadBase + index, payload[index]);
    }
    installer.write_program_word(program_abi::kRegControl, program_abi::kControlCommit);
    return expect_fault(installer);
}

bool malformed_relative_case(
    DeviceTransport& device,
    ProgramInstallTransport& installer,
    const Payload& accepted,
    std::ostream& log,
    std::ostream& errors
) {
    if (accepted[1] != 3U) return true;
    Payload malformed = accepted;
    malformed[12] = (malformed[12] & ~0x01f00000U) | (2U << 20U);
    if (!reset(device, errors)
        || !installer.write_program_word(program_abi::kRegControl,
            program_abi::kControlClear)) return false;
    for (std::uint32_t index = 0; index < malformed.size(); ++index) {
        if (!installer.write_program_word(program_abi::kPayloadBase + index,
                malformed[index])) return false;
    }
    if (!installer.write_program_word(program_abi::kRegControl,
            program_abi::kControlCommit)
        || !expect_fault(installer)
        || !reset(device, errors)) {
        errors << "DAG v3 relative-load negative failed\n";
        return false;
    }
    log << "GraphDevice-DAG-V3-NEGATIVE-V1 delta-out-of-halo=FAULT"
        << " output_published=0\n";
    return true;
}

bool invalid_matrix(
    DeviceTransport& device,
    AffineInstallTransport& affine,
    ProgramInstallTransport& program,
    const std::filesystem::path& root,
    std::ostream& log,
    std::ostream& errors
) {
    Payload payload = generated::kGraphs[0].payload;
    for (unsigned kind = 0; kind < 7U; ++kind) {
        if (!malformed_case(device, program, payload, kind)) {
            errors << "DAG invalid case failed index=" << kind << '\n';
            return false;
        }
    }
    Input input{};
    if (!load_words(root / "inputs" / "seed-1.bin", input)
        || !reset(device, errors)
        || !install_affine(affine, affine_generated::kProfiles[0], errors)
        || !stage_and_start(device, input, errors)
        || !program.write_program_word(program_abi::kRegControl,
            program_abi::kControlClear)
        || !expect_fault(program)
        || !device.write_word(abi::kRegControl, abi::kControlCancel)
        || !reset(device, errors)) {
        errors << "DAG busy mutation case failed\n";
        return false;
    }
    log << "GraphDevice-DAG-NEGATIVE-V1 partial=FAULT order=FAULT"
        << " duplicate=FAULT opcode=FAULT undefined=FAULT reserved=FAULT"
        << " missing_store=FAULT busy=FAULT cases=8 output_published=0\n";
    return true;
}

bool run_one(
    DeviceTransport& device,
    AffineInstallTransport& affine,
    ProgramInstallTransport& program,
    const generated::Graph& graph,
    const affine_generated::Profile& affine_profile,
    const std::filesystem::path& root,
    std::uint32_t seed,
    const char* mode,
    bool install_selected_program,
    std::ostream& log,
    std::ostream& errors
) {
    Input input{};
    Output fallback_output{};
    if (!load_words(root / "inputs" / ("seed-" + std::to_string(seed) + ".bin"), input)
        || !fallback(graph, affine_profile, input, fallback_output)
        || !store_output(root / ("fallback-output-" + std::string(graph.id)
            + "-seed-" + std::to_string(seed) + ".bin"), fallback_output)
        || !reset(device, errors)
        || !install_affine(affine, affine_profile, errors)
        || (install_selected_program && !install_program(program, graph, errors))
        || !stage_and_start(device, input, errors)) return false;
    if (std::string(mode) == "cancel") {
        std::uint32_t status = 0U;
        for (unsigned index = 0; index < 9U; ++index) {
            if (!read_device(device, abi::kRegStatus, status)) return false;
        }
        if (!device.write_word(abi::kRegControl, abi::kControlCancel)) return false;
        std::uint32_t polls = 0U;
        if (!wait_terminal(device, polls, status, errors)
            || (status & abi::kStatusCancelled) == 0U
            || (status & (abi::kStatusCompleted | abi::kStatusOutputValid)) != 0U
            || device.read_word(abi::kOutputBase).ok) return false;
        log << "GraphDevice-DAG-RUN-V1 graph=" << graph.id << " seed=" << seed
            << " mode=cancel status=CANCELLED output_published=0 polls=" << polls << '\n';
        return true;
    }
    std::uint32_t polls = 0U;
    std::uint32_t status = 0U;
    Output output{};
    if (!wait_terminal(device, polls, status, errors)
        || (status & (abi::kStatusCompleted | abi::kStatusOutputValid)) !=
            (abi::kStatusCompleted | abi::kStatusOutputValid)
        || !read_output(device, output, errors)
        || !store_output(root / ("private-output-" + std::string(graph.id)
            + "-seed-" + std::to_string(seed) + ".bin"), output)) return false;
    log << "GraphDevice-DAG-RUN-V1 graph=" << graph.id << " seed=" << seed
        << " mode=" << mode << " status=COMPLETED output_published=1 polls="
        << polls << '\n';
    return true;
}

}  // namespace

int run_dag(
    DeviceTransport& device,
    AffineInstallTransport& affine,
    ProgramInstallTransport& program,
    const std::filesystem::path& root,
    std::ostream& log,
    std::ostream& errors
) {
    if (!invalid_matrix(device, affine, program, root, log, errors)
        || !run_one(device, affine, program, generated::kGraphs[0],
            affine_generated::kProfiles[0], root, 1U, "complete", true, log, errors)
        || !run_one(device, affine, program, generated::kGraphs[1],
            affine_generated::kProfiles[1], root, 2U, "complete", true, log, errors)
        || !run_one(device, affine, program, generated::kGraphs[1],
            affine_generated::kProfiles[1], root, 3U, "cancel", true, log, errors)
        || !run_one(device, affine, program, generated::kGraphs[2],
            affine_generated::kProfiles[0], root, 4U, "complete", true, log, errors)
        || !run_one(device, affine, program, generated::kGraphs[0],
            affine_generated::kProfiles[0], root, 5U, "factory-restart", false, log, errors)) {
        return 1;
    }
    log << "GraphDevice-DAG-RUNTIME-V1 status=OK graphs=3 completed=4"
        << " cancelled=1 invalid_cases=8 same_rtl=1 rtl_regeneration=0"
        << " evidence=rtl-simulation-functional performance=not-measured\n";
    return 0;
}

int run_selected_dag(
    DeviceTransport& device,
    AffineInstallTransport& affine,
    ProgramInstallTransport& program,
    const std::filesystem::path& root,
    const char* graph_id,
    unsigned seed,
    std::ostream& log,
    std::ostream& errors
) {
    const generated::Graph* selected = nullptr;
    for (const generated::Graph& graph : generated::kGraphs) {
        if (std::string(graph.id) == graph_id) {
            selected = &graph;
            break;
        }
    }
    if (selected == nullptr) {
        errors << "DAG selected graph is unknown\n";
        return 2;
    }
    const affine_generated::Profile* profile = nullptr;
    if (std::string(selected->affine) == "baseline") profile = &affine_generated::kProfiles[0];
    else if (std::string(selected->affine) == "compact") profile = &affine_generated::kProfiles[1];
    else {
        errors << "DAG selected affine profile is unknown\n";
        return 2;
    }
    if (!invalid_matrix(device, affine, program, root, log, errors)
        || !run_one(device, affine, program, *selected, *profile, root, seed,
            "complete", true, log, errors)) return 1;
    log << "GraphDevice-DAG-SELECTED-RUNTIME-V1 status=OK graph=" << selected->id
        << " seed=" << seed << " completed=1 invalid_cases=8 same_rtl=1"
        << " rtl_regeneration=0 evidence=rtl-simulation-functional"
        << " performance=not-measured\n";
    return 0;
}

int run_dynamic_dag(
    DeviceTransport& device,
    AffineInstallTransport& affine,
    ProgramInstallTransport& program,
    const std::filesystem::path& root,
    const char* graph_id,
    const char* affine_name,
    const std::array<std::uint32_t, 32>& payload,
    std::uint32_t seed,
    std::ostream& log,
    std::ostream& errors
) {
    const generated::Graph graph{graph_id, affine_name, payload};
    const affine_generated::Profile* profile = nullptr;
    if (std::string(affine_name) == "baseline") profile = &affine_generated::kProfiles[0];
    else if (std::string(affine_name) == "compact") profile = &affine_generated::kProfiles[1];
    else {
        errors << "DAG dynamic affine profile is unknown\n";
        return 2;
    }
    // Keep the existing negative matrix as the preflight of the unchanged
    // executor, then execute only the host-admitted dynamic program.
    if (!invalid_matrix(device, affine, program, root, log, errors)
        || !malformed_relative_case(device, program, payload, log, errors)
        || !run_one(device, affine, program, graph, *profile, root, seed,
            "complete", true, log, errors)) return 1;
    log << "GraphDevice-DAG-DYNAMIC-RUN-V1 status=OK graph=" << graph.id
        << " seed=" << seed << " profile=" << profile->name
        << " oracle=host-independent fallback=runtime same_executor_rtl=1"
        << " evidence=rtl-simulation-functional performance=not-measured\n";
    return 0;
}

int run_dynamic_dag(
    DeviceTransport& device,
    AffineInstallTransport& affine,
    ProgramInstallTransport& program,
    const char* graph_id,
    const char* affine_name,
    const std::array<std::uint32_t, 32>& payload,
    const std::array<std::uint32_t, 324>& input,
    const std::array<std::uint32_t, 256>& oracle,
    std::uint32_t seed,
    std::ostream& log,
    std::ostream& errors
) {
    const generated::Graph graph{graph_id, affine_name, payload};
    const affine_generated::Profile* profile = nullptr;
    if (std::string(affine_name) == "baseline") profile = &affine_generated::kProfiles[0];
    else if (std::string(affine_name) == "compact") profile = &affine_generated::kProfiles[1];
    else { errors << "DAG sealed dynamic affine profile is unknown\n"; return 2; }
    Output output{};
    std::uint32_t polls = 0U;
    std::uint32_t status = 0U;
    if (!valid_fallback_program(graph.payload)
        || !reset(device, errors)
        || !install_affine(affine, *profile, errors)
        || !install_program(program, graph, errors)
        || !stage_and_start(device, input, errors)
        || !wait_terminal(device, polls, status, errors)
        || (status & (abi::kStatusCompleted | abi::kStatusOutputValid))
            != (abi::kStatusCompleted | abi::kStatusOutputValid)
        || !read_output(device, output, errors)) return 1;
    if (output != oracle) { errors << "DAG sealed dynamic output differs from oracle\n"; return 1; }
    log << "GraphDevice-DAG-SEALED-DYNAMIC-RUN-V1 status=OK graph=" << graph.id
        << " seed=" << seed << " profile=" << profile->name << " polls=" << polls
        << " oracle=independent input=sealed identity=revalidated"
        << " evidence=host-functional performance=not-measured\n";
    return 0;
}

}  // namespace raveil::graph_device
