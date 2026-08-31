#ifndef RAVEIL_GRAPH_DEVICE_UIO_H
#define RAVEIL_GRAPH_DEVICE_UIO_H

#include "graph_device_axi4lite_transport.h"

#include <cstddef>
#include <cstdint>
#include <string>

namespace raveil::graph_device {

/** Linux-only UIO map 0 backend.  It has no physical-address knowledge. */
class UioRegisterIo final : public RegisterIo {
public:
    static constexpr std::size_t kBytes = Axi4LiteTransport::kApertureBytes;
    static UioRegisterIo open_checked(const std::string& path);
    ~UioRegisterIo() override;
    UioRegisterIo(UioRegisterIo&& other) noexcept;
    UioRegisterIo& operator=(UioRegisterIo&& other) noexcept;
    UioRegisterIo(const UioRegisterIo&) = delete;
    UioRegisterIo& operator=(const UioRegisterIo&) = delete;
    DeviceRead read32(std::uint32_t byte_offset) override;
    bool write32(std::uint32_t byte_offset, std::uint32_t value) override;

private:
    UioRegisterIo(int fd, volatile std::uint32_t* words) : fd_(fd), words_(words) {}
    int fd_ = -1;
    volatile std::uint32_t* words_ = nullptr;
    void close_checked() noexcept;
};

}  // namespace raveil::graph_device

#endif
