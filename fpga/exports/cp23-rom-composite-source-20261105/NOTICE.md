# Source and licensing

The complete validated full-v006 CP23 composite source/asset closure is copied byte-for-byte under parent/, with original hashes and execution provenance. The local core copy changes only its module name and adds a positive consumer/writer idle-certificate output; core-only-delta-proof.json reverses those exact additions and requires all other text equal to the original. No v007 canonical-buffer source is selected.

The fixed ROM loader is copied unchanged from sealed cp23-fixed-rom-loader-20261105, source79e8be696098853a101002c0bf757700154db34eea95d3b8378fe4d74171b28a. GameBub-derived hardware licensing is retained under licenses/GameBub-CERN-OHL-S-2.0.txt; parent notices remain. The wrapper/test adapters are local additions. Synthetic frame0 provenance is the cp23-fixture-contract reference507ceb54c97e6a19b8bb21f5ab416dd3eb671e18.

No upstream RTL, source/export/firmware, constraints, image or hardware is modified. This is an offline local diagnostic composition, not a public codec/profile/transport implementation.
