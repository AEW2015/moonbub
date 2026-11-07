"""Isolated reset-distribution option; never alters current hardware or V026 inputs."""
from pathlib import Path
import hashlib,json,shutil
root=Path('C:/mb70');p=root/'fpga/experiments/cu66-v71/reset-bufg-v027';old=root/'dy71-v026-20261107-v001';out=root/'dy71-v027-20261107-v001';sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest();p.mkdir();out.mkdir();shutil.copytree(old/'inputs',out/'inputs')
oldtop='fpga/experiments/cu66-v71/hud-bulk-v025/moonshine_top_dy71.sv';top='fpga/experiments/cu66-v71/reset-bufg-v027/moonshine_top_dy71.sv'
s=(old/'inputs'/oldtop).read_text();needle=' wire clk=clk100,rst=joint_core_reset[3],read_clk=read_clk100,pixel_clk=pclk,pixel_reset_n=!joint_pixel_reset[3];';assert s.count(needle)==1
s=s.replace(needle,''' // A global buffer distributes the existing synchronized reset; no added stage.
 wire rst;
 BUFG core_reset_distribution(.I(joint_core_reset[3]),.O(rst));
 wire clk=clk100,read_clk=read_clk100,pixel_clk=pclk,pixel_reset_n=!joint_pixel_reset[3];''');(p/'moonshine_top_dy71.sv').write_text(s);(out/'inputs'/top).parent.mkdir(parents=True);shutil.copyfile(p/'moonshine_top_dy71.sv',out/'inputs'/top)
freeze=json.loads((old/'source-freeze.json').read_text());freeze[top]=sha(out/'inputs'/top);platform='fpga/experiments/cu66-v71/direct-system/syncsafe-math-v002/board-source-v004/constraints/platform.xdc';q=out/'inputs'/platform;s=q.read_text();assert '4459373e'in s;q.write_text(s.replace('4459373e','4459373f'));freeze[platform]=sha(q);(out/'source-freeze.json').write_text(json.dumps(freeze,indent=2)+'\n')
sel=json.loads((old/'selection.json').read_text());sel['sources']=[top if n==oldtop else n for n in sel['sources']];sel['source_sha256'].pop(oldtop);sel['source_sha256'][top]=freeze[top];sel['frozen_inputs_sha256']=freeze;sel['USERID_USR_ACCESS']='4459373f';sel['board_revision']='V027';sel['reset_distribution']='One BUFG after unchanged four ASYNC_REG stages; no added pipeline/reset exception';sel['parent_same_decoder_and_bulk']=str(old);(out/'selection.json').write_text(json.dumps(sel,indent=2)+'\n')
for n in ['synth.tcl','implementation.tcl','run-phase.py']:
 s=(old/n).read_text().replace('V026_','V027_')
 if n=='synth.tcl':assert s.count(oldtop)==1;s=s.replace(oldtop,top)
 (out/n).write_text(s)
(p/'derivation.json').write_text(json.dumps(dict(parent=str(old/'inputs'/oldtop),parent_sha256=sha(old/'inputs'/oldtop),candidate_sha256=sha(p/'moonshine_top_dy71.sv'),changes=['rst alias replaced by one explicit BUFG','Core/SPI/pixel synchronizer RTL and all consumer logic unchanged','UID3e to3f only in platform constraints'],BUFG_model='C:/Xilinx/2025.2/Vivado/data/verilog/src/unisims/BUFG.v',BUFG_model_sha256=sha(Path('C:/Xilinx/2025.2/Vivado/data/verilog/src/unisims/BUFG.v')),guide='https://docs.amd.com/r/2024.1-English/ug953-vivado-7series-libraries/BUFG',hardware=False),indent=2)+'\n')
print('V027_RESET_DISTRIBUTION_OPTION_FROZEN')
