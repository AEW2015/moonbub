#!/usr/bin/env python3
"""Inventory real retained HUD grammar and bounded control/table state."""
from pathlib import Path
import collections,hashlib,importlib.util,json,struct,sys
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3];NATIVE=ROOT/'experiments/cu66-native-v69'
s=importlib.util.spec_from_file_location('hud_partition_frozen_export',NATIVE/'export_fixtures.py');e=importlib.util.module_from_spec(s);sys.modules[s.name]=e;s.loader.exec_module(e)
CHANNEL=struct.Struct('<BBIII');PATCH=struct.Struct('<4sBBHHI16s16s')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 m=json.loads((NATIVE/'manifest.json').read_text());envelopes=collections.Counter();patches=collections.Counter();schemes=collections.Counter();residuals=collections.Counter();depths=collections.Counter();max_symbols=max_depth=max_rice_k=0;huffman_tables=huffman_bits=rice_bits=0;packet_bytes=0;raw_sizes=[]
 for case in m['cases']:
  for row in case['rows']:
   path=NATIVE/row['packet']['path'];assert sha(path)==row['packet']['sha256'];packet=path.read_bytes();o=e.w.OUTER.unpack_from(packet);hud=packet[76+o[-2]:-4];meta=e.h.f.f.hud._meta(hud);envelopes[hud[:4].decode()]+=1;packet_bytes+=len(hud);raw_sizes.append(len(packet)-len(hud)+42462)
   for kind,data in zip(meta['types'],meta['payloads']):
    magic=data[:4].decode();mode=data[5];patches[(magic,kind,mode)]+=1
    if magic in('HS32','HS33'):
     _,_,_,w,hh,size,rt,ot=PATCH.unpack_from(data);body=data[PATCH.size:-4];plain=mode&7;pos=2 if plain==2 else 10+struct.unpack_from('<I',body,6)[0]if plain==3 else 0
     for ch in range(3):
      if magic=='HS33':
       scheme,k,events,stream_size,nb=CHANNEL.unpack_from(body,pos);pos+=CHANNEL.size;schemes[scheme]+=1;max_rice_k=max(max_rice_k,k);rice_bits+=nb;stream=body[pos:pos+stream_size];pos+=stream_size+(nb+7)//8
      else:
       events=w*hh;ns,nb=struct.unpack_from('<HI',body,pos);stream_size=6+2*ns+(nb+7)//8;stream=body[pos:pos+stream_size];pos+=stream_size
      if events:
       ns,nb=struct.unpack_from('<HI',stream);assert stream_size==6+2*ns+(nb+7)//8;lengths=stream[7:6+2*ns:2];assert len(lengths)==ns;max_symbols=max(max_symbols,ns);max_depth=max(max_depth,max(lengths));depths[max(lengths)]+=1;huffman_tables+=1;huffman_bits+=nb
     assert pos==len(body)
    elif magic=='HD25'and mode in(4,5):
     body=data[PATCH.size:-4];pos=2 if mode==4 else 10+struct.unpack_from('<I',body,6)[0];residuals[body[pos]]+=1
 source={str((NATIVE/name).relative_to(ROOT)):sha(NATIVE/name)for name in('hud.hpp','bytes.hpp','generated_constants.hpp','test_hud_directed.cpp','manifest.json','hud-directed.json','negative_manifest.json')}
 result=dict(schema='cu66-v69-native-HUD-audit',source_sha256=source,frames=sum(envelopes.values()),exact_patches=sum(patches.values()),logical_words_per_frame=21120,logical_previous_and_candidate_words_bytes=84480,maximum_patch_words=7680,HUD_packet_bytes=packet_bytes,hypothetical_all_raw_HU25=dict(format_bytes_per_HUD=42462,complete_frame_bytes=sum(raw_sizes),maximum_complete_frame_bytes=max(raw_sizes),frames_exceeding_49152=sum(n>49152 for n in raw_sizes),scope='exact format size accounting only; no raw HUD packets constructed or transport throughput measured'),envelopes=dict(envelopes),patch_grammar=[dict(magic=k[0],kind=k[1],mode=k[2],count=n)for k,n in sorted(patches.items())],HS33_channel_schemes={str(k):v for k,v in sorted(schemes.items())},HD25_motion_residual_grammars={str(k):v for k,v in sorted(residuals.items())},huffman_tables=huffman_tables,maximum_observed_Huffman_symbols=max_symbols,maximum_observed_Huffman_depth=max_depth,maximum_legal_Huffman_depth=16,maximum_observed_HS33_Rice_k=max_rice_k,maximum_legal_HS33_Rice_k=14,Huffman_bit_payloads=huffman_bits,HS33_Rice_bit_payloads=rice_bits,observed_Huffman_table_depth_counts={str(k):v for k,v in sorted(depths.items())},full_FPGA_HUD_semantic_decoder=False,software_endpoint='native C++ on Linux host; no ESP32 performance or SRAM fit qualification')
 (HERE/'native-hud-audit.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:result[k]for k in('frames','exact_patches','HUD_packet_bytes','envelopes','HS33_channel_schemes','maximum_observed_Huffman_symbols','maximum_observed_Huffman_depth','maximum_observed_HS33_Rice_k')}))
if __name__=='__main__':main()
