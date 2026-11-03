#ifdef _WIN32
#include <fcntl.h>
#include <stdlib.h>
#endif
#define main upstream_main
#include "jpeg-c-model-fixed-color-source.cpp"
#undef main
int main(int argc,char**argv){
#ifdef _WIN32
_set_fmode(_O_BINARY);
#endif
return upstream_main(argc,argv);
}
