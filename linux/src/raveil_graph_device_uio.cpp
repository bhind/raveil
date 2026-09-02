#include "raveil_graph_device_uio.h"

#if !defined(__linux__)
#error "Raveil UIO transport is Linux-only"
#endif

#include <cerrno>
#include <fcntl.h>
#include <fstream>
#include <limits>
#include <stdexcept>
#include <string>
#include <sys/mman.h>
#include <sys/stat.h>
#include <sys/sysmacros.h>
#include <unistd.h>

namespace raveil::graph_device {
namespace {
bool valid(std::uint32_t offset) { return (offset & 3U) == 0U && offset <= UioRegisterIo::kBytes - 4U; }
struct UioIdentity { std::string name; unsigned number; };
UioIdentity uio_identity(const std::string& path) {
    constexpr const char* prefix = "/dev/uio";
    if (path.compare(0, 8, prefix) != 0 || path.size() == 8) return {};
    unsigned number = 0;
    for (std::size_t index = 8; index < path.size(); ++index) {
        if (path[index] < '0' || path[index] > '9') return {};
        const unsigned digit = static_cast<unsigned>(path[index] - '0');
        if (number > (std::numeric_limits<unsigned>::max() - digit) / 10U) return {};
        number = number * 10U + digit;
    }
    return {path.substr(5), number};
}
bool exact_map_size(const std::string& name) {
    std::ifstream stream("/sys/class/uio/" + name + "/maps/map0/size");
    unsigned long long size = 0;
    stream >> std::hex >> size;
    stream >> std::ws;
    return stream && stream.eof() && size == UioRegisterIo::kBytes;
}
bool exact_device_identity(const std::string& name, dev_t device) {
    std::ifstream stream("/sys/class/uio/" + name + "/dev");
    unsigned sys_major = 0;
    unsigned sys_minor = 0;
    char separator = '\0';
    stream >> sys_major >> separator >> sys_minor;
    stream >> std::ws;
    return stream && stream.eof() && separator == ':'
        && sys_major == static_cast<unsigned>(major(device))
        && sys_minor == static_cast<unsigned>(minor(device));
}
int nofollow_flag() {
#ifdef O_NOFOLLOW
    return O_NOFOLLOW;
#else
    return 0;
#endif
}
}

UioRegisterIo UioRegisterIo::open_checked(const std::string& path) {
    const UioIdentity identity = uio_identity(path);
    if (identity.name.empty()) throw std::runtime_error("UIO path must be /dev/uioN");
    const int fd = ::open(path.c_str(), O_RDWR | O_SYNC | O_CLOEXEC | nofollow_flag());
    if (fd < 0) throw std::runtime_error("UIO open failed");
    struct stat after {};
    if (fstat(fd, &after) != 0 || !S_ISCHR(after.st_mode)
        || static_cast<unsigned>(minor(after.st_rdev)) != identity.number
        || !exact_device_identity(identity.name, after.st_rdev)) {
        ::close(fd);
        throw std::runtime_error("UIO device identity differs");
    }
    if (!exact_map_size(identity.name)) { ::close(fd); throw std::runtime_error("UIO map 0 must be exactly 16 KiB"); }
    void* mapped = mmap(nullptr, kBytes, PROT_READ | PROT_WRITE, MAP_SHARED, fd, 0);
    if (mapped == MAP_FAILED) { ::close(fd); throw std::runtime_error("UIO map 0 failed"); }
    return UioRegisterIo(fd, static_cast<volatile std::uint32_t*>(mapped));
}

UioRegisterIo::~UioRegisterIo() { close_checked(); }
UioRegisterIo::UioRegisterIo(UioRegisterIo&& other) noexcept : fd_(other.fd_), words_(other.words_) { other.fd_ = -1; other.words_ = nullptr; }
UioRegisterIo& UioRegisterIo::operator=(UioRegisterIo&& other) noexcept {
    if (this != &other) { close_checked(); fd_ = other.fd_; words_ = other.words_; other.fd_ = -1; other.words_ = nullptr; }
    return *this;
}
void UioRegisterIo::close_checked() noexcept {
    if (words_ != nullptr) { munmap(const_cast<std::uint32_t*>(words_), kBytes); words_ = nullptr; }
    if (fd_ >= 0) { ::close(fd_); fd_ = -1; }
}
DeviceRead UioRegisterIo::read32(std::uint32_t byte_offset) {
    if (words_ == nullptr || !valid(byte_offset)) return {false, 0};
    return {true, words_[byte_offset / 4U]};
}
bool UioRegisterIo::write32(std::uint32_t byte_offset, std::uint32_t value) {
    if (words_ == nullptr || !valid(byte_offset)) return false;
    words_[byte_offset / 4U] = value;
    return true;
}
}  // namespace raveil::graph_device
