"""Retain the frozen overlap workload and monitors byte-for-byte except top type."""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];AREA=Path(__file__).resolve().parent
source=ROOT/'fpga/experiments/cu66-v91l-overlap-live/tb_overlap_live.cpp'
s=source.read_text()
assert 'Voverlap_live' in s
s=s.replace('Voverlap_live','Vtile_grant_live')
(AREA/'tb_tile_grant_live.cpp').write_text(s)
print('TILE_GRANT_LIVE_BENCH_GENERATED')
