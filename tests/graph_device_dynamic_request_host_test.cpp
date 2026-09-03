#include "raveil_graph_device_dynamic_request.h"

#include <exception>
#include <filesystem>

int main(int argc, char** argv) {
    if (argc != 2) return 2;
    try {
        (void)raveil::graph_device::read_dynamic_graph_device_request(
            std::filesystem::path(argv[1]));
        return 0;
    } catch (const std::exception&) {
        return 1;
    }
}
