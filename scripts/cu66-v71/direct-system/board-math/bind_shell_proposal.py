"""Complete physical dependency binding, deliberately non-buildable draft."""
from pathlib import Path
import hashlib,json
r=Path(__file__).resolve().parents[4];d=r/'fpga/experiments/cu66-v71/direct-system/board-math-v001';p=d/'physical-shell-proposal';out=p/'physical-selection-DRAFT.json';assert not out.exists();sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest();m=json.loads((d/'sources.json').read_text());sources=list(m['sources'])
extra=[r/'fpga/experiments/cu66-v71/direct-system/local-control/dy71_local_control.sv',r/'fpga/experiments/cu66-v71/system/cu71_packet_staging.sv',r/'fpga/experiments/cu66-v71/system/cu71_packet_arbiter.sv',p/'moonshine_top_dy71.sv',p/'moonshine_qspi_endpoint.sv',p/'moonshine_bus_cdc.sv']
sources.extend(f.relative_to(r).as_posix()for f in extra);assert len(sources)==len(set(sources));pins={n:sha(r/n)for n in sources};headers={}
for name in m['include_dirs']:
 for f in(r/name).glob('*.svh'):headers[f.relative_to(r).as_posix()]=sha(f)
constraints={f.relative_to(r).as_posix():sha(f)for f in(p/'constraints').iterdir()if f.is_file()}
assert 'error "DY71 physical draft blocked:'in(p/'constraints/timing-dy71-DRAFT.tcl').read_text()
platform=(p/'constraints/platform.xdc').read_text();assert platform.count('0x44593731')==2 and '0x43553731'not in platform
out.write_text(json.dumps({'status':'BLOCKED_SOURCE_BINDING_PROPOSAL_ONLY','BUILD_ALLOWED':False,'top':'moonshine_top_dy71','part':'xc7a100tcsg324-1','sources':sources,'sources_sha256':pins,'include_dirs':m['include_dirs'],'headers_sha256':headers,'constraints_sha256':constraints,'SIMULATION':False,'UID_USR_ACCESS':'0x44593731','CSR_magic':'0x44593731','ABI':'0x00010000','capabilities':'0x0f','blockers':['ExplicitSYNCsafeLCDsuccessorbindingandindependentCDCproof','ReviewedDY71localCSR/physicalQSPIbridgeintegration','Rootselectedfullsynthesis/fit/routedsetuphold/CDC/objectbindinggates'],'native_math_qualification_sha256':sha(d/'qualification-native-v001.json'),'parent_proposal_sha256':sha(p/'proposal.json'),'hardware':False,'BIT':False},indent=2)+'\n');print(sha(out))
