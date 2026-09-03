#include "VGraphDeviceAxi4LiteTop.h"
#include "verilated.h"

#include "graph_device_axi4lite_aperture_generated.h"
#include "graph_device_axi4lite_transport.h"
#include "graph_device_dag_runtime.h"
#include "raveil_graph_device_dynamic_request.h"

#include <cstdint>
#include <filesystem>
#include <cstdlib>
#include <cerrno>
#include <fcntl.h>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <sstream>
#include <string>
#include <unistd.h>

namespace {
constexpr std::uint32_t kOkay = 0;
[[noreturn]] void fail(const char* message) {
    std::cerr << "AXI4-Lite dynamic bridge: " << message << '\n';
    std::exit(1);
}

void write_exclusive(const std::filesystem::path& path, const std::string& payload) {
    int flags = O_WRONLY | O_CREAT | O_EXCL;
#ifdef O_CLOEXEC
    flags |= O_CLOEXEC;
#endif
#ifdef O_NOFOLLOW
    flags |= O_NOFOLLOW;
#endif
    const int descriptor = ::open(path.c_str(), flags, 0600);
    if (descriptor < 0) throw std::runtime_error("exclusive transcript open failed");
    std::size_t written = 0;
    while (written < payload.size()) {
        const ssize_t result = ::write(
            descriptor, payload.data() + written, payload.size() - written
        );
        if (result < 0 && errno == EINTR) continue;
        if (result <= 0) {
            ::close(descriptor);
            throw std::runtime_error("exclusive transcript write failed");
        }
        written += static_cast<std::size_t>(result);
    }
    if (::close(descriptor) != 0)
        throw std::runtime_error("exclusive transcript close failed");
}

class AxiBridge final : public raveil::graph_device::RegisterIo {
public:
    AxiBridge(VGraphDeviceAxi4LiteTop& top, std::ostream& trace) : top_(top), trace_(trace) {
        idle(); top_.aresetn = 0; tick(); top_.aresetn = 1; tick();
    }
    raveil::graph_device::DeviceRead read32(std::uint32_t address) override { return read(address); }
    bool write32(std::uint32_t address, std::uint32_t value) override { return write(address, value); }
private:
    VGraphDeviceAxi4LiteTop& top_; std::ostream& trace_; std::uint64_t sequence_ = 0;
    void idle() {
        top_.awvalid = top_.wvalid = top_.arvalid = 0; top_.bready = top_.rready = 0;
        top_.awaddr = top_.wdata = top_.wstrb = top_.araddr = 0;
    }
    void tick() { top_.aclk = 0; top_.eval(); top_.aclk = 1; top_.eval(); }
    void trace_write(std::uint32_t a, std::uint32_t d, std::uint32_t r) {
        trace_ << "AXI4LITE-TRACE-V1 seq=" << sequence_++ << " op=write address=0x"
            << std::hex << std::setw(8) << std::setfill('0') << a << " data=0x"
            << std::setw(8) << d << std::dec << " strobe=0xf response=" << r << " held_b=0\n";
    }
    void trace_read(std::uint32_t a, std::uint32_t d, std::uint32_t r) {
        trace_ << "AXI4LITE-TRACE-V1 seq=" << sequence_++ << " op=read address=0x"
            << std::hex << std::setw(8) << std::setfill('0') << a << " data=0x"
            << std::setw(8) << d << std::dec << " response=" << r << " held_r=0\n";
    }
    bool write(std::uint32_t address, std::uint32_t data) {
        top_.awaddr = address; top_.wdata = data; top_.wstrb = 0xf; top_.awvalid = top_.wvalid = 1;
        for (unsigned n = 0; n != 256; ++n) {
            top_.aclk = 0; top_.eval(); const bool fire = top_.awready && top_.wready;
            top_.aclk = 1; top_.eval(); if (fire) { top_.awvalid = top_.wvalid = 0; break; }
            if (n == 255) fail("write admission timeout");
        }
        top_.awvalid = top_.wvalid = 0;
        for (unsigned n = 0; n != 256; ++n) {
            top_.aclk = 0; top_.eval(); if (top_.bvalid) {
                const auto response = static_cast<std::uint32_t>(top_.bresp); top_.bready = 1;
                top_.aclk = 1; top_.eval(); top_.bready = 0; trace_write(address, data, response);
                return response == kOkay;
            } top_.aclk = 1; top_.eval();
        }
        fail("write response timeout");
    }
    raveil::graph_device::DeviceRead read(std::uint32_t address) {
        top_.araddr = address; top_.arvalid = 1;
        for (unsigned n = 0; n != 256; ++n) {
            top_.aclk = 0; top_.eval(); const bool fire = top_.arready;
            top_.aclk = 1; top_.eval(); if (fire) { top_.arvalid = 0; break; }
            if (n == 255) fail("read admission timeout");
        }
        top_.arvalid = 0;
        for (unsigned n = 0; n != 256; ++n) {
            top_.aclk = 0; top_.eval(); if (top_.rvalid) {
                const auto response = static_cast<std::uint32_t>(top_.rresp);
                const auto data = static_cast<std::uint32_t>(top_.rdata); top_.rready = 1;
                top_.aclk = 1; top_.eval(); top_.rready = 0; trace_read(address, data, response);
                return {response == kOkay, data};
            } top_.aclk = 1; top_.eval();
        }
        fail("read response timeout");
    }
};

}  // namespace

int main(int argc, char** argv) {
    if (argc != 2) fail("usage: VGraphDeviceAxi4LiteTop REQUEST_ROOT");
    try {
        Verilated::commandArgs(argc, argv);
        const std::filesystem::path root(argv[1]);
        const auto request = raveil::graph_device::read_dynamic_graph_device_request(root);
        const auto trace_path = root / "axi-transcript.log";
        if (std::filesystem::symlink_status(trace_path).type()
            != std::filesystem::file_type::not_found)
            throw std::runtime_error("transcript output already exists");
        std::ostringstream trace;
        VGraphDeviceAxi4LiteTop top;
        AxiBridge bridge(top, trace);
        raveil::graph_device::Axi4LiteTransport transport(
            bridge, RAVEIL_AXI_EXEC_BASE, RAVEIL_AXI_CONFIG_BASE, RAVEIL_AXI_PROGRAM_BASE);
        const int result = raveil::graph_device::run_dynamic_dag(
            transport, transport, transport, root, request.graph_id.c_str(),
            request.affine.c_str(), request.program, request.seed, std::cout, std::cerr);
        top.final();
        if (result == 0) write_exclusive(trace_path, trace.str());
        return result;
    } catch (const std::exception& error) {
        std::cerr << "AXI4-Lite dynamic bridge: " << error.what() << '\n';
        return 1;
    }
}
