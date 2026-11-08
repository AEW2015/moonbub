#pragma once
#include <stddef.h>
#include <stdint.h>
#ifdef __cplusplus
extern "C" {
#endif
int v46_hud_set_largest_probe(void*,size_t(*)());
int v46_hud_diagnostics(void*,uint64_t*,uint8_t*,size_t,size_t*);
void* v34_hud_create(size_t budget);
void v34_hud_destroy(void*);
int v34_hud_transact(void*,const uint8_t*,size_t,uint8_t*,size_t,size_t*);
int v34_hud_stats(void*,size_t* six_values);
#ifdef __cplusplus
}
#endif
