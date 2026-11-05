# Using the sealed v26 source export

The published export is sealed at manifest SHA256
`8b40f9a06d5f9634a3686d503455a7cb736c61b2e99951722cd9fdf213beba6b`.
`verify_source.py` checks its575 selected inputs and656 included artifact hashes.
Run it on the unchanged export to confirm integrity.

The export's inspect/host/metadata scripts write `checks/*`. Running them in the
sealed directory overwrites manifest-bound evidence, so a later integrity check
fails even if all575 source inputs remain unchanged. Do not use the README's
sequential validation commands directly in the sealed/published copy.

Use the external companion with a **fresh evidence directory**:

```powershell
python scripts/verify_v26_export_copy.py `
  --export firmware/exports/v26-key-diag-source-20261104 `
  --evidence evidence/v26-export-replay-001
```

Cargo/rustc can be supplied with `--cargo` and `--rustc`; the default checks are
paths,host,metadata,full-metadata. The runner verifies original integrity first,
copies all included files plus selected zero-byte fixtures, verifies the fresh
copy, runs checks there, and records new logs/output hashes in `replay-result.json`.
It rechecks all575 selected inputs and the original export after replay. It never
changes the sealed export, compiles an ESP32 target, flashes or accesses hardware.

`replay-copy/` is explicitly marked mutable and **not for builds/publication**.
Its inherited656-output manifest no longer applies after replay; this is expected,
not source corruption. New evidence is bound separately, with changed versus
unchanged inherited outputs identified. Fake-SDK host results remain distinct
from target ABI, runtime stack/heap and physical drain evidence.

For a future target check/build, start from the unchanged sealed export and its
documented esp193/IDF5.4.3 prerequisites, using a fresh short target directory.
Do not build from the replay copy or reseal changed replay evidence as if it
were the original package. This companion adds no firmware/default changes and
does not change the selected UF2/BIN/ELF or publication/hardware authority.
