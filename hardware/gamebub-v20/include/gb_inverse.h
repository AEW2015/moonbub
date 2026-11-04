#ifndef GB_V20_INVERSE_H
#define GB_V20_INVERSE_H
#include <stdint.h>
#ifdef __cplusplus
extern "C" {
#endif
/* Row-major dequantized coefficients and residuals; no prediction or clipping.
 * Legal input range is [-2048*255, +2048*255]. Both Q14 rounding boundaries
 * are floor((sum + 8192)/16384), including negative sums. No heap allocation.
 * This is a portable scalar golden reference, not synthesized/mapped RTL. */
typedef struct {
    uint32_t nonzero_coefficients;
    uint32_t nonzero_intermediates;
    uint32_t first_products;
    uint32_t second_products;
    uint32_t constant_products;
    uint32_t classification; /* 0=ZERO, 1=DC, 2=GENERAL */
} gb_v20_work;
/* 0 success, -1 null input/output, -2 out-of-contract coefficient.
 * On invalid input, output and optional work are left unchanged. */
int gb_v20_inverse_block(const int32_t input[64], int32_t output[64], gb_v20_work *work);
#ifdef __cplusplus
}
#endif
#endif
