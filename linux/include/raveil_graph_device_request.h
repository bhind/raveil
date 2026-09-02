#ifndef RAVEIL_GRAPH_DEVICE_REQUEST_H
#define RAVEIL_GRAPH_DEVICE_REQUEST_H

#include <cstdint>
#include <filesystem>

namespace raveil::graph_device {

struct AdmittedGraphDeviceRequest {
    const char* graph_id;
    std::uint32_t seed;
};

AdmittedGraphDeviceRequest admit_graph_device_request(
    const std::filesystem::path& root
);

}  // namespace raveil::graph_device

#endif
