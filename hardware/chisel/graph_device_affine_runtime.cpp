#include "graph_device_affine_runtime.h"

#include "graph_device_abi_generated.h"
#include "graph_device_affine_generated.h"

#include <array>
#include <cstdint>
#include <fstream>
#include <iomanip>
#include <string>

namespace raveil::graph_device {
namespace {

namespace generated = affine_generated;
using Input = std::array<std::uint32_t, abi::kInputCount>;
using Output = std::array<std::uint32_t, abi::kOutputCount>;

bool read_exact(std::ifstream& stream, void* data, std::size_t bytes) {
    stream.read(static_cast<char*>(data), static_cast<std::streamsize>(bytes));
    return stream.gcount() == static_cast<std::streamsize>(bytes)
        && stream.peek() == EOF;
}

std::uint32_t little_u32(const unsigned char* bytes) {
    return static_cast<std::uint32_t>(bytes[0])
        | (static_cast<std::uint32_t>(bytes[1]) << 8U)
        | (static_cast<std::uint32_t>(bytes[2]) << 16U)
        | (static_cast<std::uint32_t>(bytes[3]) << 24U);
}

bool load_input(const std::filesystem::path& path, Input& words) {
    std::array<unsigned char, abi::kInputCount * 4U> bytes{};
    std::ifstream stream(path, std::ios::binary);
    if (!stream || !read_exact(stream, bytes.data(), bytes.size())) {
        return false;
    }
    for (std::size_t index = 0; index < words.size(); ++index) {
        words[index] = little_u32(bytes.data() + index * 4U);
    }
    return true;
}

bool store_output(const std::filesystem::path& path, const Output& words) {
    std::ofstream stream(path, std::ios::binary | std::ios::trunc);
    if (!stream) {
        return false;
    }
    for (const std::uint32_t word : words) {
        const std::array<unsigned char, 4> bytes = {
            static_cast<unsigned char>(word),
            static_cast<unsigned char>(word >> 8U),
            static_cast<unsigned char>(word >> 16U),
            static_cast<unsigned char>(word >> 24U),
        };
        stream.write(
            reinterpret_cast<const char*>(bytes.data()),
            static_cast<std::streamsize>(bytes.size())
        );
    }
    return stream.good();
}

bool read_execution(
    DeviceTransport& device,
    std::uint32_t offset,
    std::uint32_t& value
) {
    const DeviceRead result = device.read_word(offset);
    if (!result.ok) {
        return false;
    }
    value = result.value;
    return true;
}

bool read_install(
    AffineInstallTransport& installer,
    std::uint32_t offset,
    std::uint32_t& value
) {
    const DeviceRead result = installer.read_install_word(offset);
    if (!result.ok) {
        return false;
    }
    value = result.value;
    return true;
}

bool reset_device(DeviceTransport& device, std::ostream& errors) {
    if (!device.write_word(abi::kRegControl, abi::kControlReset)) {
        errors << "device reset failed\n";
        return false;
    }
    return true;
}

bool verify_execution_identity(DeviceTransport& device, std::ostream& errors) {
    std::uint32_t value = 0;
    if (!read_execution(device, abi::kRegIdentity, value)
        || value != abi::kIdentity
        || !read_execution(device, abi::kRegVersion, value)
        || value != abi::kVersion
        || !read_execution(device, abi::kRegInputCount, value)
        || value != abi::kInputCount
        || !read_execution(device, abi::kRegOutputCount, value)
        || value != abi::kOutputCount) {
        errors << "execution ABI identity mismatch\n";
        return false;
    }
    return true;
}

bool verify_install_identity(
    AffineInstallTransport& installer,
    std::ostream& errors
) {
    std::uint32_t value = 0;
    if (!read_install(installer, install_abi::kRegIdentity, value)
        || value != install_abi::kIdentity
        || !read_install(installer, install_abi::kRegVersion, value)
        || value != install_abi::kVersion) {
        errors << "install ABI identity mismatch\n";
        return false;
    }
    return true;
}

bool expect_install_fault(
    AffineInstallTransport& installer,
    std::ostream& errors,
    const char* label
) {
    std::uint32_t status = 0;
    if (!read_install(installer, install_abi::kRegStatus, status)
        || (status & install_abi::kStatusFault) == 0U) {
        errors << "invalid install did not fault case=" << label << '\n';
        return false;
    }
    return true;
}

bool install_profile(
    AffineInstallTransport& installer,
    const generated::Profile& profile,
    std::ostream& errors
) {
    if (!installer.write_install_word(
            install_abi::kRegControl,
            install_abi::kControlClear
        )) {
        errors << "configuration clear failed profile=" << profile.name << '\n';
        return false;
    }
    std::uint32_t status = 0;
    std::uint32_t count = 0;
    if (!read_install(installer, install_abi::kRegStatus, status)
        || (status & install_abi::kStatusLoading) == 0U
        || (status & (install_abi::kStatusInstalled | install_abi::kStatusFault)) != 0U
        || !read_install(installer, install_abi::kRegPayloadCount, count)
        || count != 0U) {
        errors << "configuration clear state failed profile=" << profile.name << '\n';
        return false;
    }
    for (std::uint32_t index = 0; index < profile.payload.size(); ++index) {
        if (!installer.write_install_word(
                install_abi::kPayloadBase + index,
                profile.payload[index]
            )
            || !read_install(installer, install_abi::kRegPayloadCount, count)
            || count != index + 1U) {
            errors << "configuration payload failed profile=" << profile.name
                   << " word=" << index << '\n';
            return false;
        }
    }
    if (!installer.write_install_word(
            install_abi::kRegControl,
            install_abi::kControlCommit
        )
        || !read_install(installer, install_abi::kRegStatus, status)
        || (status & install_abi::kStatusInstalled) == 0U
        || (status & (install_abi::kStatusLoading | install_abi::kStatusFault)) != 0U) {
        errors << "configuration commit failed profile=" << profile.name << '\n';
        return false;
    }
    for (std::uint32_t index = 0; index < profile.digest.size(); ++index) {
        std::uint32_t word = 0;
        if (!read_install(
                installer,
                install_abi::kRegDigestBase + index,
                word
            )
            || word != profile.digest[index]) {
            errors << "live configuration digest mismatch profile=" << profile.name
                   << " word=" << index << '\n';
            return false;
        }
    }
    return true;
}

bool stage(
    DeviceTransport& device,
    const Input& input,
    std::ostream& errors
) {
    for (std::uint32_t index = 0; index < input.size(); ++index) {
        if (!device.write_word(abi::kInputBase + index, input[index])) {
            errors << "input staging failed word=" << index << '\n';
            return false;
        }
    }
    return true;
}

bool poll_terminal(
    DeviceTransport& device,
    std::uint32_t& status,
    std::uint32_t& polls,
    std::ostream& errors
) {
    for (polls = 1; polls <= abi::kMaxStatusPolls; ++polls) {
        if (!read_execution(device, abi::kRegStatus, status)) {
            errors << "status read failed\n";
            return false;
        }
        if ((status & abi::kStatusFault) != 0U) {
            errors << "execution device reported a fault\n";
            return false;
        }
        if ((status & (abi::kStatusCompleted | abi::kStatusCancelled)) != 0U) {
            return true;
        }
    }
    errors << "finite status timeout exceeded\n";
    return false;
}

bool run_success(
    DeviceTransport& device,
    AffineInstallTransport& installer,
    const generated::Profile& profile,
    const std::filesystem::path& root,
    unsigned seed,
    bool restart,
    std::ostream& log,
    std::ostream& errors
) {
    Input input{};
    if (!reset_device(device, errors)
        || !install_profile(installer, profile, errors)
        || !load_input(root / "inputs" / ("seed-" + std::to_string(seed) + ".bin"), input)
        || !stage(device, input, errors)
        || !device.write_word(abi::kRegControl, abi::kControlStart)) {
        errors << "affine run setup failed profile=" << profile.name
               << " seed=" << seed << '\n';
        return false;
    }
    std::uint32_t status = 0;
    std::uint32_t polls = 0;
    if (!poll_terminal(device, status, polls, errors)
        || (status & abi::kStatusCompleted) == 0U
        || (status & (abi::kStatusCancelled | abi::kStatusBusy)) != 0U
        || (status & abi::kStatusOutputValid) == 0U) {
        errors << "affine completion failed profile=" << profile.name
               << " seed=" << seed << '\n';
        return false;
    }
    Output output{};
    for (std::uint32_t index = 0; index < output.size(); ++index) {
        if (!read_execution(device, abi::kOutputBase + index, output[index])) {
            errors << "private output read failed profile=" << profile.name
                   << " seed=" << seed << " word=" << index << '\n';
            return false;
        }
    }
    if (!store_output(
            root / ("private-output-" + std::string(profile.name)
                + "-seed-" + std::to_string(seed) + ".bin"),
            output
        )) {
        errors << "private output storage failed profile=" << profile.name << '\n';
        return false;
    }
    std::uint32_t checksumLow = 0;
    std::uint32_t checksumHigh = 0;
    if (!read_execution(device, abi::kRegChecksumLow, checksumLow)
        || !read_execution(device, abi::kRegChecksumHigh, checksumHigh)) {
        errors << "checksum read failed profile=" << profile.name << '\n';
        return false;
    }
    const std::uint64_t checksum = static_cast<std::uint64_t>(checksumLow)
        | (static_cast<std::uint64_t>(checksumHigh) << 32U);
    log << "GraphDevice-AFFINE-RUN-V1 profile=" << profile.name
        << " seed=" << seed << " status=COMPLETED staged_words=324 polls="
        << polls << " output_valid=1 output_words=256 active_outputs="
        << profile.activeOutputs << " checksum=" << std::hex << std::setw(16)
        << std::setfill('0') << checksum << std::dec << std::setfill(' ')
        << " restart=" << (restart ? 1 : 0) << '\n';
    return true;
}

bool run_cancel(
    DeviceTransport& device,
    AffineInstallTransport& installer,
    const generated::Profile& profile,
    const std::filesystem::path& root,
    std::ostream& log,
    std::ostream& errors
) {
    Input input{};
    if (!reset_device(device, errors)
        || !install_profile(installer, profile, errors)
        || !load_input(root / "inputs" / "seed-3.bin", input)
        || !stage(device, input, errors)
        || !device.write_word(abi::kRegControl, abi::kControlStart)) {
        errors << "affine cancel setup failed\n";
        return false;
    }
    std::uint32_t status = 0;
    for (unsigned index = 0; index < 17U; ++index) {
        if (!read_execution(device, abi::kRegStatus, status)
            || (status & (abi::kStatusFault | abi::kStatusCompleted)) != 0U) {
            errors << "affine cancel precondition failed\n";
            return false;
        }
    }
    if (!device.write_word(abi::kRegControl, abi::kControlCancel)) {
        errors << "affine cancel command failed\n";
        return false;
    }
    std::uint32_t polls = 0;
    if (!poll_terminal(device, status, polls, errors)
        || (status & abi::kStatusCancelled) == 0U
        || (status & (abi::kStatusCompleted | abi::kStatusOutputValid
            | abi::kStatusBusy)) != 0U
        || device.read_word(abi::kOutputBase).ok) {
        errors << "affine cancel terminal state failed\n";
        return false;
    }
    log << "GraphDevice-AFFINE-CANCEL-V1 profile=" << profile.name
        << " seed=3 status=CANCELLED output_valid=0 output_words=0"
        << " blocked_read=1 published=0\n";
    return true;
}

bool run_invalid_matrix(
    DeviceTransport& device,
    AffineInstallTransport& installer,
    const std::filesystem::path& root,
    std::ostream& log,
    std::ostream& errors
) {
    const generated::Profile& baseline = generated::kProfiles[0];

    if (!reset_device(device, errors)
        || !installer.write_install_word(install_abi::kRegControl, install_abi::kControlClear)
        || !installer.write_install_word(install_abi::kPayloadBase, baseline.payload[0])
        || !installer.write_install_word(install_abi::kRegControl, install_abi::kControlCommit)
        || !expect_install_fault(installer, errors, "partial")) {
        return false;
    }
    if (!reset_device(device, errors)
        || !installer.write_install_word(install_abi::kRegControl, install_abi::kControlClear)
        || !installer.write_install_word(install_abi::kPayloadBase + 1U, baseline.payload[1])
        || !expect_install_fault(installer, errors, "order")) {
        return false;
    }
    if (!reset_device(device, errors)
        || !installer.write_install_word(install_abi::kRegControl, install_abi::kControlClear)
        || !installer.write_install_word(install_abi::kPayloadBase, baseline.payload[0])
        || !installer.write_install_word(install_abi::kPayloadBase, baseline.payload[0])
        || !expect_install_fault(installer, errors, "duplicate")) {
        return false;
    }
    if (!reset_device(device, errors)
        || !installer.write_install_word(install_abi::kRegControl, install_abi::kControlClear)) {
        return false;
    }
    for (std::uint32_t index = 0; index < baseline.payload.size(); ++index) {
        std::uint32_t word = baseline.payload[index];
        if (index == 8U) {
            word ^= 1U;
        }
        if (!installer.write_install_word(install_abi::kPayloadBase + index, word)) {
            errors << "digest-negative payload write failed\n";
            return false;
        }
    }
    if (!installer.write_install_word(install_abi::kRegControl, install_abi::kControlCommit)
        || !expect_install_fault(installer, errors, "digest")) {
        return false;
    }

    Input input{};
    if (!reset_device(device, errors)
        || !install_profile(installer, baseline, errors)
        || !load_input(root / "inputs" / "seed-3.bin", input)
        || !stage(device, input, errors)
        || !device.write_word(abi::kRegControl, abi::kControlStart)
        || !installer.write_install_word(install_abi::kRegControl, install_abi::kControlClear)
        || !expect_install_fault(installer, errors, "busy")
        || !device.write_word(abi::kRegControl, abi::kControlCancel)) {
        return false;
    }
    std::uint32_t status = 0;
    std::uint32_t polls = 0;
    if (!poll_terminal(device, status, polls, errors)
        || (status & abi::kStatusCancelled) == 0U) {
        errors << "busy-negative cleanup failed\n";
        return false;
    }
    log << "GraphDevice-AFFINE-NEGATIVE-V1 partial=FAULT order=FAULT"
        << " duplicate=FAULT digest=FAULT busy=FAULT mutation=0 cases=5\n";
    return true;
}

}  // namespace

int run_affine(
    DeviceTransport& device,
    AffineInstallTransport& installer,
    const std::filesystem::path& evidence_root,
    std::ostream& log,
    std::ostream& errors
) {
    if (!reset_device(device, errors)
        || !verify_execution_identity(device, errors)
        || !verify_install_identity(installer, errors)
        || !run_invalid_matrix(device, installer, evidence_root, log, errors)
        || !run_success(
            device, installer, generated::kProfiles[0], evidence_root,
            1U, false, log, errors
        )
        || !run_success(
            device, installer, generated::kProfiles[1], evidence_root,
            2U, false, log, errors
        )
        || !run_cancel(
            device, installer, generated::kProfiles[1], evidence_root,
            log, errors
        )
        || !run_success(
            device, installer, generated::kProfiles[1], evidence_root,
            4U, true, log, errors
        )) {
        return 1;
    }
    log << "GraphDevice-AFFINE-RUNTIME-V1 status=OK completed=3 cancelled=1"
        << " resets=10 profiles=2 invalid_cases=5"
        << " evidence=rtl-simulation-functional performance=not-measured\n";
    return 0;
}

}  // namespace raveil::graph_device
