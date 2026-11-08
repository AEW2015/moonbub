"""Prepare only a reviewed-source board overlay. Does not launch Vivado or program hardware."""
from pathlib import Path
import argparse,shutil,json,hashlib
p=Path(__file__).resolve().parents[1];base=Path('C:/moon/dev/dy71-v027-20261107-v001')
a=argparse.ArgumentParser();a.add_argument('--out',type=Path,default=Path('C:/moon/builds/stb1-v001'));args=a.parse_args();out=args.out.resolve()
assert out.is_relative_to(Path('C:/moon/builds').resolve()) and not out.exists(),'new isolated builds directory required'
assert json.loads((p/'evidence/pins08/result.json').read_text())['cases']==9
assert 'STAGING_BURST_UNIT_PASS cases13' in (p/'evidence/unit06/run.log').read_text()
assert 'STAGING_BURST_FULL256_PASS' in (p/'evidence/full256-unit02/run.log').read_text()
out.mkdir(parents=True);shutil.copytree(base/'inputs',out/'inputs')
old='fpga/experiments/cu66-v71/hud-bulk-v025/dy71_local_control_bulk_v025.sv'
newdir='fpga/experiments/cu66-v71/staging-burst-v1-20261108'
newcontrol=newdir+'/dy71_local_control_staging_burst_v1.sv';newfifo=newdir+'/cu71_staging_burst_v1.sv'
(out/'inputs'/old).unlink();(out/'inputs'/newdir).mkdir(parents=True)
control=(p/'rtl/dy71_local_control_staging_burst_v1.sv').read_text()
assert control.count('module dy71_local_control_staging_burst_v1(')==1
# Module-identifier-only adaptation preserves exact V027 top and hierarchy/constraints.
(out/'inputs'/newcontrol).write_text(control.replace('module dy71_local_control_staging_burst_v1(','module dy71_local_control_bulk_v025('))
shutil.copyfile(p/'rtl/cu71_staging_burst_v1.sv',out/'inputs'/newfifo)
s=(base/'synth.tcl').read_text().replace('read_verilog -sv [file join $root '+old+']','read_verilog -sv [file join $root '+newfifo+']\nread_verilog -sv [file join $root '+newcontrol+']').replace('V027_SYNTHESIS_CONSTRAINTS_COMPLETE_NO_BIT','STB1_SYNTHESIS_CONSTRAINTS_COMPLETE_NO_BIT')
(out/'synth.tcl').write_text(s);(out/'implementation.tcl').write_text((base/'implementation.tcl').read_text().replace('V027_BOARD_REPORTS_COMPLETE_NO_BIT_OR_HARDWARE','STB1_BOARD_REPORTS_COMPLETE_NO_BIT_OR_HARDWARE'))
selection=json.loads((base/'selection.json').read_text());selection.update(board_revision='STB1_PROTOTYPE_NOT_V027',ABI='00030000',capabilities='3f',USERID_USR_ACCESS='UNASSIGNED_REQUIRES_REVIEW_BEFORE_BIT',hardware='NOT_PROGRAMMED',qualification='FUNCTIONAL_SUBSYSTEM_ONLY_ROUTE_NOT_RUN')
selection['sources']=[newcontrol if n==old else n for n in selection['sources']]+[newfifo]
(out/'selection.json').write_text(json.dumps(selection,indent=2))
sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
freeze={f.relative_to(out/'inputs').as_posix():sha(f)for f in sorted((out/'inputs').rglob('*'))if f.is_file()}
(out/'source-freeze.json').write_text(json.dumps(freeze,indent=2))
constraints={n:h for n,h in freeze.items()if n.endswith(('.xdc','.tcl'))};assert all((base/'inputs'/n).is_file() and sha(base/'inputs'/n)==h for n,h in constraints.items())
shutil.copyfile(p/'tools/board_run_phase.py',out/'run-phase.py')
manifest={'base':str(base),'prototype':str(p),'source_freeze_sha256':sha(out/'source-freeze.json'),'compiled_sources':selection['sources'],'removed_control':old,'added_sources':[newcontrol,newfifo],'module_only_adaptation':'prototype new control module identifier renamed to original module name in board copy; top/hierarchy unchanged','all_constraint_files_byte_identical':True,'constraint_hashes':constraints,'top_byte_identical':sha(base/'inputs/fpga/experiments/cu66-v71/reset-bufg-v027/moonshine_top_dy71.sv')==sha(out/'inputs/fpga/experiments/cu66-v71/reset-bufg-v027/moonshine_top_dy71.sv'),'script_sha256':{n:sha(out/n)for n in ['synth.tcl','implementation.tcl','run-phase.py']},'USERCODE':'UNASSIGNED_NO_BIT_COMMAND','RTL_BUILD':'NOT_LAUNCHED','bytes':sum(f.stat().st_size for f in out.rglob('*')if f.is_file()),'maximum_path_chars':max(map(lambda f:len(str(f)),out.rglob('*')))}
(out/'overlay-binding.json').write_text(json.dumps(manifest,indent=2));print(json.dumps(manifest,indent=2))
