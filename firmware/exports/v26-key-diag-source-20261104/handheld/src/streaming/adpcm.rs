//! Independent Microsoft WAV IMA ADPCM stereo blocks; no allocation.
//! Multiplicative delta rounding matches frozen independent FFmpeg WAV decode.
pub const BLOCK: usize = 512;
pub const FRAMES: usize = 505;
pub const PCM_BYTES: usize = FRAMES * 4;
const INDEX: [i32; 16] = [-1, -1, -1, -1, 2, 4, 6, 8, -1, -1, -1, -1, 2, 4, 6, 8];
const STEP: [i32; 89] = [
    7, 8, 9, 10, 11, 12, 13, 14, 16, 17, 19, 21, 23, 25, 28, 31, 34, 37, 41, 45, 50, 55, 60, 66,
    73, 80, 88, 97, 107, 118, 130, 143, 157, 173, 190, 209, 230, 253, 279, 307, 337, 371, 408, 449,
    494, 544, 598, 658, 724, 796, 876, 963, 1060, 1166, 1282, 1411, 1552, 1707, 1878, 2066, 2272,
    2499, 2749, 3024, 3327, 3660, 4026, 4428, 4871, 5358, 5894, 6484, 7132, 7845, 8630, 9493,
    10442, 11487, 12635, 13899, 15289, 16818, 18500, 20350, 22385, 24623, 27086, 29794, 32767,
];
pub fn validate(block: &[u8]) -> Result<(), ()> {
    if block.len() != BLOCK || block[2] > 88 || block[6] > 88 || block[3] != 0 || block[7] != 0 {
        Err(())
    } else {
        Ok(())
    }
}
fn sample(code: u8, predictor: &mut i32, index: &mut i32) -> i16 {
    let step = STEP[*index as usize];
    let diff = (step * (2 * (code as i32 & 7) + 1)) >> 3;
    if code & 8 != 0 {
        *predictor -= diff
    } else {
        *predictor += diff
    }
    *predictor = (*predictor).clamp(-32768, 32767);
    *index = (*index + INDEX[code as usize]).clamp(0, 88);
    *predictor as i16
}
pub fn decode(block: &[u8], pcm: &mut [u8]) -> Result<(), ()> {
    validate(block)?;
    if pcm.len() != PCM_BYTES {
        return Err(());
    }
    let mut pred = [
        i16::from_le_bytes([block[0], block[1]]) as i32,
        i16::from_le_bytes([block[4], block[5]]) as i32,
    ];
    let mut index = [block[2] as i32, block[6] as i32];
    for ch in 0..2 {
        pcm[ch * 2..ch * 2 + 2].copy_from_slice(&(pred[ch] as i16).to_le_bytes());
    }
    for group in 0..63 {
        for ch in 0..2 {
            for byte in 0..4 {
                let value = block[8 + group * 8 + ch * 4 + byte];
                for nibble in 0..2 {
                    let code = (value >> (nibble * 4)) & 15;
                    let v = sample(code, &mut pred[ch], &mut index[ch]);
                    let at = (1 + group * 8 + byte * 2 + nibble) * 4 + ch * 2;
                    pcm[at..at + 2].copy_from_slice(&v.to_le_bytes());
                }
            }
        }
    }
    Ok(())
}
#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn zero_and_channel_predictors() {
        let mut b = [0; 512];
        b[0..2].copy_from_slice(&1000i16.to_le_bytes());
        b[4..6].copy_from_slice(&(-1000i16).to_le_bytes());
        let mut out = [0; 2020];
        decode(&b, &mut out).unwrap();
        for x in out.chunks_exact(4) {
            assert_eq!(i16::from_le_bytes([x[0], x[1]]), 1000);
            assert_eq!(i16::from_le_bytes([x[2], x[3]]), -1000)
        }
    }
    #[test]
    fn invalid_headers_do_not_touch_output() {
        for at in [2, 3, 6, 7] {
            let mut b = [0; 512];
            b[at] = 255;
            let mut out = [17; 2020];
            assert!(decode(&b, &mut out).is_err());
            assert!(out.iter().all(|x| *x == 17));
        }
        assert!(validate(&[0; 511]).is_err());
    }
    #[test]
    fn nibble_and_channel_interleave() {
        let mut b = [0; 512];
        b[8] = 0x71;
        b[12] = 0xf9;
        let mut out = [0; 2020];
        decode(&b, &mut out).unwrap();
        assert_eq!(&out[4..12], &[2, 0, 254, 255, 15, 0, 241, 255]);
    }
    #[test]
    fn clips_predictor_and_index() {
        let mut p = 32767;
        let mut i = 88;
        assert_eq!(sample(7, &mut p, &mut i), 32767);
        assert_eq!(i, 88);
        p = -32768;
        assert_eq!(sample(15, &mut p, &mut i), -32768);
        i = 0;
        sample(0, &mut p, &mut i);
        assert_eq!(i, 0);
    }
}
