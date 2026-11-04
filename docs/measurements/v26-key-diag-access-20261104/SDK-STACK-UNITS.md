# Stack watermark units for this ESP-IDF build

The sealed v24 ESP-IDF bindings define `StackType_t = u8` at line18308.
The installed IDF5.4.3 Xtensa `portmacro.h` defines `portSTACK_TYPE uint8_t`
at lines88/91. Its FreeRTOS `tasks.c` counts fill bytes and divides that count
by `sizeof(StackType_t)` at lines4798–4810; `uxTaskGetStackHighWaterMark` returns
that count at lines4858–4878. Thus a raw watermark unit is **one byte** in this
specific build. Generic upstream task.h prose describing four-byte words must
not override the actual selected Xtensa type and implementation.

V24's compiled SDK configuration is byte-identical to v22, so the earlier raw
USB716, AV3212, producer1916 and consumer11100 observations can be interpreted
as byte counts under that SDK binding. They remain historical sampled minima,
not current measurements, stack allocation sizes or proofs of safety. A new
build must retain/recheck its own bindings. Neither these units nor selected
ELF frames establishes the worst nested SDK/FFI/runtime call chain.

Primary local inputs:

- `C:/Users/lavat/.espressif/esp-idf/v5.4.3/components/freertos/FreeRTOS-Kernel/tasks.c`
- `C:/Users/lavat/.espressif/esp-idf/v5.4.3/components/freertos/FreeRTOS-Kernel/portable/xtensa/include/freertos/portmacro.h`
- `firmware/experiments/v24-runtime-diagnostics-20261104/evidence/compiled-idf-bindings.rs`

The bindings SHA-256 is
`c721d4d5940dcd68b8e54cdc266224773fc221af2b3c3624862b24afa33de991`,
also recorded by the sealed v24 build manifest. Source files remain unchanged.

`tasks.c` SHA-256:
`e9b5676a35b5b8b9173b4b187173f9cbfae4808ddc902be2f25f0f9e5f463538`.
`portmacro.h` SHA-256:
`3d7bfecf4a97874a41678612daf71ce763e29fc84ca8a81edba6739aa5e3d867`.
