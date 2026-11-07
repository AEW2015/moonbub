#pragma once
#include <stddef.h>
#include <stdint.h>
#ifdef __cplusplus
extern "C" {
#endif
void* v34_hud_create(size_t budget);
void v34_hud_destroy(void*);
int v34_hud_transact(void*,const uint8_t*,size_t,uint8_t*,size_t,size_t*);
int v34_hud_stats(void*,size_t* six_values);
#ifdef __cplusplus
}
#endif
