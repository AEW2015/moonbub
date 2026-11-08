#!/usr/bin/env python3
"""Prepare source/models or run the bounded actual threshold qualification."""
import subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];HELP=ROOT/'scripts/cu66-v107/count_threshold'
if '--prepare' in sys.argv:
 for name in ('prepare.py','model.py','verification.py'):subprocess.run([sys.executable,str(HELP/name)],cwd=ROOT,check=True)
else:subprocess.run([sys.executable,str(HELP/'qualify.py'),*sys.argv[1:]],cwd=ROOT,check=True)
