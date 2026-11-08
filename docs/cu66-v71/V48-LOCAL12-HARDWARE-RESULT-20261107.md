# V48 local twelve-frame hardware pass

One finite trial from local`.33` to`.157:5535` passed:12accepted/12presented/0rejected/0underruns, all253,440HUDwords written and compared, zero native allocation failures. Sender session13880965209089969554/source`.33:60102` received all12matching presentation replies, exited0 and stopped without retry. The camera showed the final expected game scene/HUD.

Selected V48 ELF`93a389adb4e5bf88fa9eb5d28fc3d82abdb012e4fb647cd50f81196c917aab74`; unchanged V027 BIT`9922aa617c21a03e8a31f932d45e22d905e91d4e263ef593692898d363d07dee`, checked DONE1/USERCODE4459373f. Native sources are exactly V47's larger-first decoder. The local controller verified a live owned uploader and remaining wait before arming once; no`.47`relay was used.

Receiver elapsed21,923,482microseconds. Arena cap98,304/live42,408/peak88,830,2,260allocation calls,0failures. Result-time health73,356free/21,504largest; network-worker stack low2,904, native minimumfree17,996. Full43-record export and read-only re-export independently validated with identical checksum`bbee1904`. Underlying USB loss count remains unknown. Detailed timing ring retains only ordinals9–11; nine earlier frame timings were omitted.

Retained timings:

| Frame | Native CPU | HUD write | HUD readback |
|---:|---:|---:|---:|
|9|212.382ms|291.388ms|275.783ms|
|10|196.723ms|289.892ms|322.480ms|
|11|124.060ms|291.166ms|276.801ms|

This bounded diagnostic includes stop/wait ingress and full HUD readback. It is not30fps,120-second playback, or a measured unique-camera-frame rate. Source is the packaged historical cohort, not the requested full120-second source. Compared with V46, host/source path and new USB/static layout also changed; this is not an isolated causal A/B attribution to allocation order alone.

Automation gates observed after app-only bootstrap: nonce PING passed; Windows vendor interface0 now usesWINUSB with problemcode0; read-only GET_INFO returned serial802C0E7A and actual Rev4.1hardware`0x01040100`. CDC continued working. USB lab revision4800 is not hardware identity.

One subsequent nonce-tagged software REBOOT was acknowledged. A continuously armed monitor observed USB disappearance/return. The first controller failed because Windows listed COM3 before it was openable; it issued no second reset. An independent read-only capture verified fresh reset reason3, lower uptime48.702376s versus430.812358s, exact same ELF and166,464free/86,016largest. This establishes that reboot occurred; the original controller failure is retained. The port-open wait was then fixed offline and requires a new explicit qualification case. No claim of a battery-rail cold cycle is made.

Evidence: `C:/moon/dev/evidence/v48-v027-local-20261107-run01`, including`NETWORK-RESULT.json`, `REBOOT-RESULT.json`, raw USB, source/hash-bound local controller command, sender log, validated exports and camera capture. [Machine-readable network result](V48-LOCAL12-HARDWARE-RESULT-20261107.json).
