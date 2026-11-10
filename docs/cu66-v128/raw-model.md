# V128 raw tuple algebra model

The independent Python model compares V127's selected 72-bit tuple validation with V128's two direct lane decisions followed by the ingress selector. It uses the V127 integration source index for the old selected scratch and `source-map.json` for all 18 current selected sources, including the four V128 replacements.

- Result: **PASS_MODEL_ONLY**, 71,066 generated records, 568,528 per-phase decision comparisons, zero mismatches.
- Coverage includes every 3-bit phase encoding, both independent ingress selector values, both scratch stored-format values, directed valid and invalid records, signed value boundaries, 17-bit block cast boundaries, full-width epoch/count/written/previous-position cases, and deterministic random valid plus single-field mutation populations.
- Selected-record error class follows the old sequential priority: code 2 for a selected epoch mismatch; code 3 for another selected input error. Invalid data in only the unselected lane does not affect the result.
- The old source's actual band test is transcribed from its `zigzag()` and `band_matches()` functions. At equal blocks, sparse ordering uses the arbitrary stored 64-bit rank mask exactly as implemented. Literal zigzag order is checked only for a mask derived from the owned previous-position threshold.
- Source hashes and detailed coverage are in [`raw-model.json`](../../experiments/python-gamebub-v128/python-model/raw-model.json). Model script SHA-256: `319f4c0794c16763357a9856acf79f002bceca6ff8ac815a8cc0756735e06025`.

This is an algebra model only: no RTL run, exhaustive sequential check, timing measurement, or timing qualification.
