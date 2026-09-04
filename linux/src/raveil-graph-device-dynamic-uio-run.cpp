#include "raveil_graph_device_dynamic_request.h"
#include "raveil_graph_device_uio.h"
#include "graph_device_dag_runtime.h"

#include <filesystem>
#include <iostream>
#include <sstream>

int main(int argc, char** argv) {
    if (argc != 3) {
        std::cerr << "usage: raveil-graph-device-dynamic-uio-run /dev/uioN SEALED_ROOT\n";
        return 2;
    }
    try {
        const auto admitted = raveil::graph_device::read_sealed_dynamic_graph_device_request(
            std::filesystem::path(argv[2]));
        // No device side effect is permitted before this exact sealed-v2
        // identity/version admission returns successfully.
        auto io = raveil::graph_device::UioRegisterIo::open_checked(argv[1]);
        raveil::graph_device::Axi4LiteTransport transport(io, 0x0000U, 0x2000U, 0x3000U);
        std::ostringstream runtime_log;
        std::ostringstream runtime_errors;
        const int result = raveil::graph_device::run_dynamic_dag(
            transport, transport, transport, admitted.request.graph_id.c_str(),
            admitted.request.affine.c_str(), admitted.request.program,
            admitted.request.input, admitted.oracle, admitted.request.seed,
            runtime_log, runtime_errors);
        if (result != 0) { std::cerr << runtime_errors.str(); return result; }
        std::cout << "GraphDevice-DYNAMIC-UIO-TRANSPORT-V1 runtime_return=0"
            << " graph_output=unpromoted evidence=host-functional"
            << " device_opened=1 hardware=not-verified performance=not-measured\n";
        return 0;
    } catch (const std::exception& error) {
        std::cerr << "dynamic UIO Graph-device runner: " << error.what() << '\n';
        return 1;
    }
}
