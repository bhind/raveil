#include "raveil_graph_device_dynamic_request.h"

#include <exception>
#include <filesystem>
#include <iostream>
#include <string>

int main(int argc, char** argv) {
    if (argc != 2 && argc != 3) return 2;
    try {
        if (argc == 3 && std::string(argv[2]) == "--projected") {
            (void)raveil::graph_device::read_projected_dynamic_graph_device_request(std::filesystem::path(argv[1]));
        } else {
            if (argc != 2) return 2;
            (void)raveil::graph_device::read_dynamic_graph_device_request(std::filesystem::path(argv[1]));
        }
        return 0;
    } catch (const std::exception& error) {
        std::cerr << error.what() << '\n';
        return 1;
    }
}
