#include "raveil_graph_device_request.h"

#include <cassert>
#include <string>

int main(int argc, char** argv) {
    assert(argc == 3);
    const auto request = raveil::graph_device::admit_graph_device_request(argv[1]);
    assert(std::string(request.graph_id) == argv[2]);
    return 0;
}
