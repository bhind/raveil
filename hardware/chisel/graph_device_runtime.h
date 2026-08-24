#ifndef RAVEIL_GraphDevice_RUNTIME_H
#define RAVEIL_GraphDevice_RUNTIME_H

#include <cstdint>
#include <filesystem>
#include <iosfwd>

namespace raveil::graph_device {

struct DeviceRead {
    bool ok;
    std::uint32_t value;
};

/** Transport-neutral, pointer-free word-addressed device boundary. */
class DeviceTransport {
public:
    virtual ~DeviceTransport() = default;
    virtual DeviceRead read_word(std::uint32_t word_offset) = 0;
    virtual bool write_word(std::uint32_t word_offset, std::uint32_t value) = 0;
};

int run_mvp(
    DeviceTransport& device,
    const std::filesystem::path& evidence_root,
    std::ostream& log,
    std::ostream& errors
);

}  // namespace raveil::graph_device

#endif
