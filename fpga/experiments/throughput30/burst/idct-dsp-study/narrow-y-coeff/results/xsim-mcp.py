import json,subprocess,sys,uuid
command=['docker','exec','-i','amd-ross-mcp-1000-2162172','bash','-c','source /opt/Xilinx/2025.2/Vivado/settings64.sh >&2; exec /opt/ross/server --stdio-bridge']
p=subprocess.Popen(command,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=sys.stderr,text=True,bufsize=1)
sequence=0
def send(method,params):
 global sequence
 sequence+=1;msg={'jsonrpc':'2.0','id':sequence,'method':method,'params':params}
 p.stdin.write(json.dumps(msg)+'\n');p.stdin.flush()
 while True:
  line=p.stdout.readline()
  if not line:raise RuntimeError('MCP bridge closed')
  response=json.loads(line)
  if response.get('id')==sequence:
   if 'error' in response:raise RuntimeError(response['error'])
   return response['result']
def call(name,args):
 result=send('tools/call',{'name':name,'arguments':args})
 print(json.dumps({'tool':name,'result':result}),flush=True)
 if result.get('isError'):raise RuntimeError(name+' failed')
 blocks=result.get('content',[])
 texts=[x.get('text','') for x in blocks if x.get('type')=='text']
 for item in texts:
  try:
   decoded=json.loads(item)
   if decoded.get('exit_code',0)!=0 or decoded.get('status')=='error':raise RuntimeError(str(decoded))
   return decoded
  except json.JSONDecodeError:pass
 return result.get('structuredContent',result)
sid=None
try:
 send('initialize',{'protocolVersion':'2024-11-05','capabilities':{},'clientInfo':{'name':'abort-study','version':'1'}})
 p.stdin.write(json.dumps({'jsonrpc':'2.0','method':'notifications/initialized'})+'\n');p.stdin.flush()
 info=call('vivado_start',{'working_dir':'/ross-work/idct-y-equivalence','session_type':'general'});sid=info.get('session_id')
 if not sid:raise RuntimeError('no Vivado session')
 call('vivado_todos',{'session_id':sid,'operation':'plan','title':'Y-stage coefficient XSim equivalence','tasks':[{'id':'setup','content':'Create isolated XSim project'},{'id':'run','content':'Execute bounded self-checking stage test'},{'id':'review','content':'Check logs and retain result'}]})
 call('vivado_todos',{'session_id':sid,'operation':'update','id':'setup','status':'active'})
 project='project-'+uuid.uuid4().hex[:8]
 cmd=f'set installed_parts [get_parts -quiet]; create_project abort_project /ross-work/idct-y-equivalence/{project} -part [lindex $installed_parts 0]; add_files -fileset sim_1 -norecurse [glob /ross-work/idct-y-equivalence/src/*.v /ross-work/idct-y-equivalence/src/*.sv]; set_property verilog_define {{SIMULATION}} [get_filesets sim_1]; set_property top tb_narrow_y [get_filesets sim_1]; set_property target_simulator XSim [current_project]; set_property xsim.simulate.runtime 2ms [get_filesets sim_1]; update_compile_order -fileset sim_1' 
 call('vivado_execute',{'session_id':sid,'command':cmd})
 call('vivado_todos',{'session_id':sid,'operation':'update','id':'setup','status':'done'})
 call('vivado_todos',{'session_id':sid,'operation':'update','id':'run','status':'active'})
 result=call('vivado_execute',{'session_id':sid,'command':'launch_simulation -simset sim_1 -mode behavioral'})
 output=result.get('output','')
 if 'NARROW_Y_COEFF_EQ_PASS' not in output or 'Fatal:' in output or 'ERROR:' in output: raise RuntimeError('Missing clean PASS')
 call('vivado_todos',{'session_id':sid,'operation':'update','id':'run','status':'done'})
 call('vivado_log_messages',{'session_id':sid,'filter':'errors','max_messages':30})
 call('vivado_todos',{'session_id':sid,'operation':'update','id':'review','status':'done'})
 call('vivado_stop',{'session_id':sid});sid=None
finally:
 if sid:
  try:call('vivado_stop',{'session_id':sid})
  except Exception as e:print('Vivado cleanup failed:',e,file=sys.stderr)
 p.stdin.close();p.terminate();p.wait(timeout=5)
