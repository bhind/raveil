#include "raveil_graph_device_uio.h"
#include "raveil_graph_device_request.h"
#include "graph_device_dag_runtime.h"
#include <filesystem>
#include <iostream>
#include <sstream>

int main(int argc, char** argv) {
    if (argc != 3) { std::cerr << "usage: raveil-graph-device-uio-run /dev/uioN REQUEST_ROOT\n"; return 2; }
    try {
        const std::filesystem::path root(argv[2]);
        const auto admitted = raveil::graph_device::admit_graph_device_request(root);
        const auto graph_id = admitted.graph_id;
        const auto seed = admitted.seed;
        auto io = raveil::graph_device::UioRegisterIo::open_checked(argv[1]);
        // These are relative words in the contract's fixed 16 KiB aperture;
        // this runner intentionally has no physical-address input.
        raveil::graph_device::Axi4LiteTransport transport(io, 0x0000U, 0x2000U, 0x3000U);
        std::ostringstream runtime_log;
        std::ostringstream runtime_errors;
        const int result = raveil::graph_device::run_selected_dag(
            transport, transport, transport, root, graph_id, seed,
            runtime_log, runtime_errors
        );
        if (result != 0) {
            std::cerr << runtime_errors.str();
            return result;
        }
        std::cout << "GraphDevice-UIO-TRANSPORT-V1 runtime_return=0"
            << " graph_output=unpromoted evidence=linux-uio-transport-unverified"
            << " same_rtl=not-verified hardware=not-verified\n";
        return 0;
    } catch (const std::exception& error) {
        std::cerr << "UIO Graph-device runner: " << error.what() << '\n';
        return 1;
    }
}
