#include "gb_inverse.h"
#include <string.h>

static const int32_t q14[8][8] = {
    {5793,5793,5793,5793,5793,5793,5793,5793},
    {8035,6811,4551,1598,-1598,-4551,-6811,-8035},
    {7568,3135,-3135,-7568,-7568,-3135,3135,7568},
    {6811,-1598,-8035,-4551,4551,8035,1598,-6811},
    {5793,-5793,-5793,5793,5793,-5793,-5793,5793},
    {4551,-8035,1598,6811,-6811,-1598,8035,-4551},
    {3135,-7568,7568,-3135,-3135,7568,-7568,3135},
    {1598,-4551,6811,-8035,8035,-6811,4551,-1598}
};

static int32_t rounded_q14(int64_t sum) {
    const int64_t biased = sum + INT64_C(8192);
    /* C division truncates toward zero. Use explicit floor for negatives;
     * signed right shift is deliberately avoided for compiler portability. */
    return (int32_t)(biased >= 0 ? biased / INT64_C(16384)
        : -((-biased + INT64_C(16383)) / INT64_C(16384)));
}

int gb_v20_inverse_block(const int32_t input[64], int32_t output[64], gb_v20_work *work) {
    int32_t middle[64];
    int64_t accum[8];
    gb_v20_work counted = {0,0,0,0,0,0};
    uint32_t ac = 0;
    unsigned r, c, k;
    if (input == 0 || output == 0) return -1;
    for (k = 0; k < 64; ++k) {
        if (input[k] < -522240 || input[k] > 522240) return -2;
        counted.nonzero_coefficients += input[k] != 0;
        if (k) ac |= (uint32_t)(input[k] != 0);
    }
    if (!ac) {
        const int32_t value = input[0] == 0 ? 0
            : rounded_q14((int64_t)rounded_q14((int64_t)input[0] * 5793) * 5793);
        for (k = 0; k < 64; ++k) output[k] = value;
        counted.classification = input[0] == 0 ? 0 : 1;
        counted.constant_products = input[0] == 0 ? 0 : 2;
        if (work) *work = counted;
        return 0;
    }
    counted.classification = 2;
    for (r = 0; r < 8; ++r) {
        memset(accum, 0, sizeof(accum));
        for (k = 0; k < 8; ++k) {
            const int32_t value = input[8*r+k];
            if (value == 0) continue;
            for (c = 0; c < 8; ++c) accum[c] += (int64_t)value * q14[k][c];
            counted.first_products += 8;
        }
        for (c = 0; c < 8; ++c) {
            middle[8*r+c] = rounded_q14(accum[c]);
            counted.nonzero_intermediates += middle[8*r+c] != 0;
        }
    }
    for (c = 0; c < 8; ++c) {
        memset(accum, 0, sizeof(accum));
        for (k = 0; k < 8; ++k) {
            const int32_t value = middle[8*k+c];
            if (value == 0) continue;
            for (r = 0; r < 8; ++r) accum[r] += (int64_t)value * q14[k][r];
            counted.second_products += 8;
        }
        for (r = 0; r < 8; ++r) output[8*r+c] = rounded_q14(accum[r]);
    }
    if (work) *work = counted;
    return 0;
}
