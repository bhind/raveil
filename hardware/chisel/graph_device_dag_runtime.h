#ifndef RAVEIL_GRAPH_DEVICE_DAG_RUNTIME_H
#define RAVEIL_GRAPH_DEVICE_DAG_RUNTIME_H

#include "graph_device_affine_runtime.h"

#include <cstdint>
#include <filesystem>
#include <iosfwd>

namespace raveil::graph_device {

namespace program_abi {
inline constexpr std::uint32_t kIdentity = 0x52565001U;
inline constexpr std::uint32_t kVersion = 1U;
inline constexpr std::uint32_t kRegIdentity = 0U;
inline constexpr std::uint32_t kRegVersion = 1U;
inline constexpr std::uint32_t kRegControl = 4U;
inline constexpr std::uint32_t kRegStatus = 5U;
inline constexpr std::uint32_t kRegPayloadCount = 6U;
inline constexpr std::uint32_t kRegDigestBase = 16U;
inline constexpr std::uint32_t kPayloadBase = 256U;
inline constexpr std::uint32_t kPayloadCount = 32U;
inline constexpr std::uint32_t kControlClear = 1U;
inline constexpr std::uint32_t kControlCommit = 2U;
inline constexpr std::uint32_t kStatusLoading = 1U;
inline constexpr std::uint32_t kStatusInstalled = 2U;
inline constexpr std::uint32_t kStatusFault = 4U;
}  // namespace program_abi

class ProgramInstallTransport {
public:
    virtual ~ProgramInstallTransport() = default;
    virtual DeviceRead read_program_word(std::uint32_t word_offset) = 0;
    virtual bool write_program_word(
        std::uint32_t word_offset,
        std::uint32_t value
    ) = 0;
};

int run_dag(
    DeviceTransport& device,
    AffineInstallTransport& affine,
    ProgramInstallTransport& program,
    const std::filesystem::path& evidence_root,
    std::ostream& log,
    std::ostream& errors
);

}  // namespace raveil::graph_device

#endif
