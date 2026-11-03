// Windows binary stdio adapter only. Decoder algorithms remain upstream source.
#ifdef _WIN32
#include <fcntl.h>
#include <stdlib.h>
#endif
#define main core_jpeg_upstream_main
#include "../fpga/vendor/core_jpeg/c_model/main.cpp"
#undef main

int main(int argc, char **argv) {
#ifdef _WIN32
    _set_fmode(_O_BINARY); // upstream fopen("w") otherwise expands pixel0A to0D0A
#endif
    return core_jpeg_upstream_main(argc, argv);
}
