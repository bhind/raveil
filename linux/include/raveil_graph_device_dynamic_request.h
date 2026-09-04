#ifndef RAVEIL_GRAPH_DEVICE_DYNAMIC_REQUEST_H
#define RAVEIL_GRAPH_DEVICE_DYNAMIC_REQUEST_H

#include <array>
#include <cstdint>
#include <filesystem>
#include <string>

namespace raveil::graph_device {

struct DynamicGraphDeviceRequest {
    std::string graph_id;
    std::string affine;
    std::uint32_t seed = 0;
    std::array<std::uint32_t, 32> program{};
    std::array<std::uint32_t, 16> configuration{};
    std::array<std::uint32_t, 324> input{};
};

/** Python has verified the original seal before producing this private root. */
struct ProjectedDynamicGraphDeviceRequest {
    DynamicGraphDeviceRequest request;
    std::uint32_t version = 0;
    std::array<std::uint32_t, 256> oracle{};
};

DynamicGraphDeviceRequest read_dynamic_graph_device_request(
    const std::filesystem::path& root
);

ProjectedDynamicGraphDeviceRequest read_projected_dynamic_graph_device_request(
    const std::filesystem::path& root
);

}  // namespace raveil::graph_device

#endif
