"""Build upstream and separately labeled fixed-color C-model test oracles.

Only the generated copy changes color arithmetic to RTL's specified fixedpoint
coefficients. The vendor entropy parser, tables, IDCT and block addressing stay
unchanged. Windows binary stdio is applied to both variants.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess


def main():
    root = Path(__file__).resolve().parent.parent
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--compiler", type=Path, default=Path("C:/msys64/ucrt64/bin/g++.exe"))
    args = parser.parse_args()
    source = root / "fpga/vendor/core_jpeg/c_model"
    output = root / "host/evidence"
    original = (source / "main.cpp").read_text()
    changes = {
        "int r = 128 + y[i] + (cr[i] * 1.402);": "int r = 128 + y[i] + ((cr[i] * 5743) >> 12);",
        "int g = 128 + y[i] - (cb[i] * 0.34414) - (cr[i] * 0.71414);": "int g = 128 + y[i] - ((cb[i] * 1410) >> 12) - ((cr[i] * 2925) >> 12);",
        "int b = 128 + y[i] + (cb[i] * 1.772);": "int b = 128 + y[i] + ((cb[i] * 7258) >> 12);",
    }
    fixed = original
    for before, after in changes.items():
        if fixed.count(before) != 1:
            raise RuntimeError("upstream source changed; review C-model color adapter")
        fixed = fixed.replace(before, after)
    fixed_source = output / "jpeg-c-model-fixed-color-source.cpp"
    fixed_source.write_text(fixed)
    wrapper = output / "jpeg-c-model-fixed-color-main.cpp"
    wrapper.write_text('#ifdef _WIN32\n#include <fcntl.h>\n#include <stdlib.h>\n#endif\n'
                       '#define main upstream_main\n#include "jpeg-c-model-fixed-color-source.cpp"\n#undef main\n'
                       'int main(int argc,char**argv){\n#ifdef _WIN32\n_set_fmode(_O_BINARY);\n#endif\nreturn upstream_main(argc,argv);\n}\n')
    env = os.environ.copy()
    env["PATH"] = str(args.compiler.parent) + os.pathsep + env["PATH"]
    inputs = [source / "main.cpp", *sorted(source.glob("*.h")), root / "host/cmodel_main.cpp", wrapper, fixed_source]
    manifest = {"scope": "software oracle build; no hardware execution", "changes": changes,
                "compiler": subprocess.check_output([str(args.compiler), "--version"], env=env, text=True).splitlines()[0],
                "source_files": {str(path.relative_to(root)): hashlib.sha256(path.read_bytes()).hexdigest() for path in inputs},
                "variants": {}}
    jpeg = root / "host/fixtures/pattern-720x480-420-q65.jpg"
    for name, entry in (("upstream", root / "host/cmodel_main.cpp"), ("fixed-color", wrapper)):
        executable = output / ("jpeg-c-model-" + name + ".exe")
        reference = output / ("pattern-c-model" + ("-fixed-color" if name != "upstream" else "") + ".ppm")
        command = [str(args.compiler), "-std=c++17", "-O2", "-I" + str(source), str(entry), "-o", str(executable)]
        build = subprocess.run(command, env=env, capture_output=True, text=True)
        (output / ("c-model-build-" + name + ".log")).write_text(build.stdout + build.stderr)
        build.check_returncode()
        decoded = subprocess.run([str(executable), str(jpeg), str(reference)], env=env, capture_output=True, text=True)
        (output / ("c-model-run-" + name + ".log")).write_text(decoded.stdout + decoded.stderr)
        decoded.check_returncode()
        manifest["variants"][name] = {"command": command, "reference": str(reference.relative_to(root)),
                                      "reference_sha256": hashlib.sha256(reference.read_bytes()).hexdigest(),
                                      "executable_sha256": hashlib.sha256(executable.read_bytes()).hexdigest()}
    (output / "c-model-build-manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps(manifest["variants"], indent=2))


if __name__ == "__main__":
    main()
