"""Replay the offline bridge using only its preserved Python dependencies.

No socket, serial, firmware or hardware operation is provided.
"""
from pathlib import Path
import argparse
import importlib.util
import sys

sys.dont_write_bytecode = True
here = Path(__file__).resolve().parent

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--count', type=int, choices=range(1, 13), default=1)
    parser.add_argument('--rgb24-npy', type=Path)
    args = parser.parse_args()
    output = args.output.resolve()
    if not output.is_relative_to(Path('C:/moon').resolve()) or output.exists():
        raise ValueError('Use a fresh output path under C:/moon')
    deps = here / 'dependencies'
    if not (deps / 'source-bindings.json').is_file():
        raise ValueError('Preserved dependency snapshot is required')
    spec = importlib.util.spec_from_file_location('offline_bridge_replay', here/'bridge.py')
    bridge = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = bridge
    spec.loader.exec_module(bridge)
    bridge.EXPERIMENTS = deps
    canvases = (bridge.np.load(args.rgb24_npy, allow_pickle=False)
                if args.rgb24_npy else bridge.np.stack([bridge.synthetic(i) for i in range(args.count)]))
    if len(canvases) != args.count:
        raise ValueError('Explicit count must match the prepared source array')
    bridge.encode_sequence(canvases, output)

if __name__ == '__main__':
    main()
