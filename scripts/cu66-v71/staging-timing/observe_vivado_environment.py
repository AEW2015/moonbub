"""Read selected non-secret environment keys from one explicitly named own process."""
import argparse,ctypes,json
from ctypes import wintypes
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--pid',type=int,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
k=ctypes.WinDLL('kernel32',use_last_error=True);nt=ctypes.WinDLL('ntdll')
k.OpenProcess.restype=wintypes.HANDLE;k.OpenProcess.argtypes=[wintypes.DWORD,wintypes.BOOL,wintypes.DWORD]
k.ReadProcessMemory.argtypes=[wintypes.HANDLE,ctypes.c_void_p,ctypes.c_void_p,ctypes.c_size_t,ctypes.POINTER(ctypes.c_size_t)]
k.CloseHandle.argtypes=[wintypes.HANDLE]
class PBI(ctypes.Structure):_fields_=[('reserved',ctypes.c_void_p),('peb',ctypes.c_void_p),('reserved2',ctypes.c_void_p*2),('pid',ctypes.c_size_t),('reserved3',ctypes.c_void_p)]
h=k.OpenProcess(0x410,False,a.pid)
if not h:raise ctypes.WinError(ctypes.get_last_error())
try:
 def read(addr,n):
  buf=ctypes.create_string_buffer(n);got=ctypes.c_size_t()
  if not k.ReadProcessMemory(h,addr,buf,n,ctypes.byref(got)):raise ctypes.WinError(ctypes.get_last_error())
  return buf.raw[:got.value]
 b=PBI();size=wintypes.ULONG();status=nt.NtQueryInformationProcess(h,0,ctypes.byref(b),ctypes.sizeof(b),ctypes.byref(size))
 if status:raise RuntimeError('NtQueryInformationProcess status '+hex(status&0xffffffff))
 pointer=lambda addr:int.from_bytes(read(addr,8),'little')
 params=pointer(b.peb+0x20);env=pointer(params+0x80)
 data=bytearray()
 # Read small pages to avoid crossing the valid environment allocation.
 for off in range(0,512*1024,256):
  data.extend(read(env+off,256))
  text=data.decode('utf-16-le',errors='surrogatepass')
  if '\0\0'in text:break
 else:raise RuntimeError('Environment terminator not found within bound')
 allowed={'TEMP','TMP','TMPDIR','TMP_DIR','TEMPDIR','XILINX_VIVADO','XILINX_LOCAL_USER_DATA','HOME','HOMEDRIVE','HOMEPATH','USERPROFILE','SYSTEMROOT','COMSPEC','NODEFAULTCURRENTDIRECTORYINEXEPATH'}
 observed={}
 for item in text.split('\0\0',1)[0].split('\0'):
  if '='in item:
   name,value=item.split('=',1)
   if name.upper()in allowed:observed[name]=value
 a.output.parent.mkdir(parents=True,exist_ok=True)
 if a.output.exists():raise FileExistsError(a.output)
 a.output.write_text(json.dumps(dict(pid=a.pid,process_memory_readonly=True,environment_keys_filtered=True,keys=observed,scope='Read actual64bit process PEB/process-parameters environment; no process mutation or secret keys output'),indent=2)+'\n')
 print(json.dumps(observed,indent=2))
finally:k.CloseHandle(h)
