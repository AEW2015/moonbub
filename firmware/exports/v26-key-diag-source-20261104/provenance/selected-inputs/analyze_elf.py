"""Selected actual Xtensa frames/calls. Deliberately not a stack-safety proof."""
from pathlib import Path
import hashlib,json,re,subprocess,sys
P=Path(__file__).resolve().parent;E=P/'evidence';ELF=P/(sys.argv[1] if len(sys.argv)>1 else 'release-key-resource')/'moonshine-rev4.elf'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 tool=next((Path.home()/'.espressif/tools/esp-clang').glob('**/llvm-objdump.exe'))
 raw=subprocess.check_output([str(tool),'--syms','--demangle',str(ELF)],text=True)
 (E/'elf-symbols-v26.log').write_text(raw)
 symbols=[]
 for line in raw.splitlines():
  m=re.match(r'^([0-9a-f]+)\s+\w+\s+F\s+(\S+)\s+([0-9a-f]+)\s+(.+)$',line)
  if m:symbols.append({'address':int(m[1],16),'size':int(m[3],16),'name':m[4]})
 byaddr={s['address']:s for s in symbols};selected={}
 predicates={
  'USBcommand':lambda n:n.endswith('handheld::usb_test::command'),
  'USBtask':lambda n:'usb_test::start::{closure#0}'in n,
  'USBruntime':lambda n:n.endswith('handheld::usb_diag::runtime'),
  'USBvideo':lambda n:n.endswith('handheld::usb_diag::video'),
  'SDKlogger':lambda n:'esp_idf_svc::log::'in n,
  'KeyUSB':lambda n:'handheld::key_diag_usb::'in n,
  'KeyCore':lambda n:'handheld::key_diag_core::'in n,
  'KeyPages':lambda n:'handheld::key_diag_pages::'in n,
  'Dispatch':lambda n:'handheld::diag_dispatch::'in n,
  'Admission':lambda n:'handheld::core_admission::'in n,
  'Coordinator':lambda n:'handheld::core_coordinator::'in n,
  'CoreAccess':lambda n:'handheld::core_access::'in n,
  'FpgaProgram':lambda n:'handheld::device::drivers::fpga::Fpga<'in n and n.endswith('::program'),
  'AVrun':lambda n:n.endswith('handheld::streaming::audio::run'),
  'AVstep':lambda n:n.endswith('handheld::streaming::audio::step'),
 }
 for label,pred in predicates.items():
  for row in symbols:
   if pred(row['name']):selected.setdefault(row['address'],dict(row,labels=[]))['labels'].append(label)
 frames=[]
 for address,row in sorted(selected.items()):
  command=[str(tool),'-d','--demangle',f'--start-address={address}',f"--stop-address={address+row['size']}",str(ELF)]
  asm=subprocess.check_output(command,text=True);name=f'frame-v26-{address:08x}.log';(E/name).write_text(asm)
  entry=re.search(r'\bentry\s+a1,\s*(\d+)',asm)
  instructions=[x for x in asm.splitlines() if re.match(r'^\s*[0-9a-f]+:',x)]
  direct=[]
  for line in instructions:
   m=re.search(r'\bcall(?:0|4|8|12)\s+0x([0-9a-f]+)\s+<(.+)>',line)
   if m:direct.append({'address':'0x'+m[1],'symbol':m[2],'target_bytes':byaddr.get(int(m[1],16),{}).get('size')})
  frames.append(dict(row,frame_bytes=int(entry[1])if entry else None,disassembly=name,prologue=instructions[:8],direct_calls=direct,indirect_calls=sum(bool(re.search(r'\bcallx(?:0|4|8|12)\b',x))for x in instructions),unknown_decode=sum('<unknown>'in x for x in instructions)))
 missing=[label for label,pred in predicates.items() if not any(pred(s['name'])for s in symbols)]
 old=json.loads((P.parents[0]/'v24-runtime-diagnostics-20261104/evidence/stack-frames-v24.json').read_text())
 result={'elf_sha256':sha(ELF),'tool':str(tool),'tool_sha256':sha(tool),'frames':frames,'not_found_or_inlined':missing,'baseline_v24':{'elf_sha256':old['elf_sha256'],'frames':[{k:x.get(k)for k in ['label','symbol','frame_bytes']}for x in old['frames']]},'declared_stacks_bytes':{'USB':4096,'AV':8192,'KeyDiag':4096},'KeyDiag_stack_status':'PROVISIONAL_PENDING_STATIC_REVIEW_AND_PHYSICAL_GATE','stack_units':'Verify compiled StackType_t=u8 in build manifest; historical minima are not this build measurements.','limits':['Selected entry a1 prologues and direct/indirect calls only, not a closed maximum call graph.','Compiler-inlined code belongs to caller frame; NOT_FOUND_OR_INLINED is not zero stack.','Indirect SDK/FFI/logger/formatter calls, interrupt/context and thread runtime overhead remain open.','No physical stack minima, heap peak, logger framing, query overhead or synchronous SPI WCET measured.'],'physical_gates':'NOT_RUN'}
 (E/'stack-frames-v26.json').write_text(json.dumps(result,indent=2)+'\n')
 rows=['# Selected v26 ELF frames — static review only','','Individual frames cannot establish task headroom. KeyDiag4096 remains provisional.','','| Labels | Frame bytes | Symbol |','| --- | ---: | --- |']
 rows += [f"| {','.join(f['labels'])} | {f['frame_bytes']} | `{f['name']}` |"for f in frames]
 rows+=['','Not found or inlined: '+', '.join(missing),'','Physical stack/logging/heap/SPI WCET gates: NOT_RUN.','']
 (E/'stack-frames-v26.md').write_text('\n'.join(rows))
 print('Selected',len(frames),'actual frames; full stack bound NOT_PROVEN')
 for f in frames:
  if any(x in f['labels']for x in ['USBcommand','KeyUSB','KeyPages','KeyCore','Dispatch','FpgaProgram']):print(','.join(f['labels']),f['frame_bytes'],f['name'])
if __name__=='__main__':main()
