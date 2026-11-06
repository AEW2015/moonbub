"""Isolate cache-hit responses from the physical memory arbiter in a new variant."""
from pathlib import Path
import hashlib,json,re
r=Path(__file__).resolve().parents[3];p=r/'fpga/experiments/cu66-v71/memory';sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
s=(p/'cu71_word_bridge_burst.sv').read_text().replace('module cu71_word_bridge_burst #(', 'module cu71_word_bridge_burst_cache #(')
s=s.replace(' logic background_pending,hold_for_lcd;', ' logic background_pending,hold_for_lcd;logic[1:0]fast_hit;logic[3:0]scheduled_pending;')
start=s.index('  background_pending=');end=s.index('  p0_ready=',start)
schedule=s[start:end].replace('pending[','scheduled_pending[')
s=s[:start]+'''  fast_hit[0]=pending[0]&&!writing[0]&&cache_valid[0]&&cache_tag[0]==address[0][23:3];
  fast_hit[1]=pending[1]&&!writing[1]&&cache_valid[1]&&cache_tag[1]==address[1][23:3];
  scheduled_pending=pending&~{2'b00,fast_hit};
'''+schedule+s[end:]
pattern=r'end else if\(selected<2&&!writing\[selected\].*?cache_hits<=cache_hits\+1;\n     end else begin'
s,n=re.subn(pattern,'end else begin',s,flags=re.S);assert n==1
s=s.replace('IDLE:if(any_pending&&!hold_for_lcd)', 'IDLE:if((|scheduled_pending)&&!hold_for_lcd)')
s=s.replace('   case(state)', '''   // Completed-cache data is private to each reader. An active aliasing
   // write has invalidated its block at grant, so no stale in-flight hit can
   // bypass it. Different-client unsynchronized operations remain unordered.
   for(integer i=0;i<2;i=i+1)if(fast_hit[i])begin
    pending[i]<=0;response_error[i]<=0;response_data[i]<={112'd0,cache_data[i*8+address[i][2:0]]};response_valid[i]<=1;
   end
   if(|fast_hit)cache_hits<=cache_hits+32'(fast_hit[0])+32'(fast_hit[1]);
   case(state)''',1)
assert 'cache_hits<=cache_hits+1;'not in s
(p/'cu71_word_bridge_burst_cache.sv').write_text(s,newline='\n')
t=(p/'cu71_memory_system_burst.sv').read_text().replace('module cu71_memory_system_burst #(', 'module cu71_memory_system_burst_cache #(').replace(' cu71_word_bridge_burst bridge(', ' cu71_word_bridge_burst_cache bridge(')
(p/'cu71_memory_system_burst_cache.sv').write_text(t,newline='\n')
(p/'cache-derivation.json').write_text(json.dumps({'parents':{n:sha(p/n)for n in ['cu71_memory_system_burst.sv','cu71_word_bridge_burst.sv']},'candidates':{n:sha(p/n)for n in ['cu71_memory_system_burst_cache.sv','cu71_word_bridge_burst_cache.sv']},'scope':'Privatecachehitresponsemaycompletewhileanotherclientownscontroller. ActualmemorytransactionsretainLCD2:1lookahead/backgroundRR;writealiasinvalidationsunchanged. Noport/clock/PHYchanges.','hardware':False},indent=2)+'\n')
print('PREPARED_INDEPENDENT_CACHE_HIT_VARIANT')
