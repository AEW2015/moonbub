# Native EC92 development notes

The first exploratory unit compile rejected a misleading-indentation warning (`if (!first) ...; first=false;`) under `-Werror`; the statements were split before the passing qualification build.

The first retained full campaign failed before its first source because `/usr/bin/time` is absent in the build container. Its unmodified report and source snapshots remain under `attempts/20261107T045924767360Z-e2b9131d/`. The repaired helper queries its own process peak RSS with Linux `getrusage(RUSAGE_SELF)` instead. No container packages were installed.

EC92 is a software research profile. Raw fallback is canonical: if either frozen encoder replaces its coded streams with RAW, all sixteen requested candidates use RAW with wire mask zero. Otherwise a particular mixed combination uses RAW only when its selected stream payload would be at least the raw coefficient size. Discarded candidates remain included in native generation timing. This policy preserves correctness and bounds; it does not claim to recover unavailable coded streams after a frozen encoder chooses RAW.
