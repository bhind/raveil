#include "raveil_graph_device_dynamic_request.h"
#include "graph_device_axi4lite_transport.h"
#include "graph_device_dag_runtime.h"

#include <filesystem>
#include <sstream>

namespace raveil::graph_device {
int run_projected_dynamic_graph_host_adapter(RegisterIo& io,
                                             const std::filesystem::path& projected_root,
                                             std::ostream& log, std::ostream& errors) {
    try {
        const auto admitted = read_projected_dynamic_graph_device_request(projected_root);
        Axi4LiteTransport transport(io, 0x0000U, 0x2000U, 0x3000U);
        return run_dynamic_dag(
            transport, transport, transport, admitted.request.graph_id.c_str(), admitted.request.affine.c_str(),
            admitted.request.program, admitted.request.input, admitted.oracle, admitted.request.seed,
            log, errors);
    } catch (const std::exception& error) {
        errors << "projected dynamic host adapter: " << error.what() << '\n';
        return 1;
    }
}
}  // namespace raveil::graph_device
