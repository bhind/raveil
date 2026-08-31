#ifndef RAVEIL_GRAPH_DEVICE_AXI4LITE_TRANSPORT_H
#define RAVEIL_GRAPH_DEVICE_AXI4LITE_TRANSPORT_H

#include "graph_device_dag_runtime.h"

#include <cstdint>
#include <limits>

namespace raveil::graph_device {

/** A deliberately small, relative 32-bit register aperture. */
class RegisterIo {
public:
    virtual ~RegisterIo() = default;
    virtual DeviceRead read32(std::uint32_t byte_offset) = 0;
    virtual bool write32(std::uint32_t byte_offset, std::uint32_t value) = 0;
};

/** Maps the three specified word-addressed ABIs into one 16 KiB aperture. */
class Axi4LiteTransport final : public DeviceTransport,
                                public AffineInstallTransport,
                                public ProgramInstallTransport {
public:
    static constexpr std::uint32_t kApertureBytes = 0x4000U;
    static constexpr std::uint32_t kExecutionBytes = 0x2000U;
    static constexpr std::uint32_t kConfigBytes = 0x1000U;
    static constexpr std::uint32_t kProgramBytes = 0x1000U;
    Axi4LiteTransport(RegisterIo& io, std::uint32_t exec_base,
                      std::uint32_t config_base, std::uint32_t program_base)
        : io_(io), exec_base_(exec_base), config_base_(config_base), program_base_(program_base) {}

    DeviceRead read_word(std::uint32_t word) override { return read(exec_base_, kExecutionBytes, word); }
    bool write_word(std::uint32_t word, std::uint32_t value) override { return write(exec_base_, kExecutionBytes, word, value); }
    DeviceRead read_install_word(std::uint32_t word) override { return read(config_base_, kConfigBytes, word); }
    bool write_install_word(std::uint32_t word, std::uint32_t value) override { return write(config_base_, kConfigBytes, word, value); }
    DeviceRead read_program_word(std::uint32_t word) override { return read(program_base_, kProgramBytes, word); }
    bool write_program_word(std::uint32_t word, std::uint32_t value) override { return write(program_base_, kProgramBytes, word, value); }

private:
    RegisterIo& io_;
    const std::uint32_t exec_base_, config_base_, program_base_;
    static bool offset(std::uint32_t base, std::uint32_t span,
                       std::uint32_t word, std::uint32_t* result) {
        if ((base & 3U) != 0U || (span & 3U) != 0U || span < 4U
            || base >= kApertureBytes || span > kApertureBytes - base
            || word > (std::numeric_limits<std::uint32_t>::max() / 4U)) return false;
        const std::uint32_t bytes = word * 4U;
        if (bytes > span - 4U) return false;
        *result = base + bytes;
        return true;
    }
    DeviceRead read(std::uint32_t base, std::uint32_t span, std::uint32_t word) {
        std::uint32_t address = 0;
        return offset(base, span, word, &address) ? io_.read32(address) : DeviceRead{false, 0};
    }
    bool write(std::uint32_t base, std::uint32_t span,
               std::uint32_t word, std::uint32_t value) {
        std::uint32_t address = 0;
        return offset(base, span, word, &address) && io_.write32(address, value);
    }
};

}  // namespace raveil::graph_device

#endif
