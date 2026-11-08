from pathlib import Path
import json,struct,hashlib
p=Path(__file__).resolve().parent;H=struct.Struct('<4sBBHHI16s16s');CH=struct.Struct('<BBIII');S=struct.Struct('<HI');cases=[];modes={};grammars=set();schemes=set();rles=set();fields=set()
for folder in ['positive03','stream04']:
 for line in(p/folder/'index.tsv').read_text().splitlines():
  name,path,ref,expected,w,hh,success=line.split('\t')
  if success!='1':continue
  packet=(p/folder/path).read_bytes();magic,ver,mode,pw,ph,size,rt,ot=H.unpack_from(packet);magic=magic.decode();assert (pw,ph)==(int(w),int(hh))and size==len(packet)-H.size-4;modes.setdefault(magic,set()).add(mode);body=packet[H.size:-4];pos=0;entry={'name':name,'folder':folder,'magic':magic,'mode':mode,'words':pw*ph}
  plain=(mode&7)if magic.startswith('HS')else 2 if mode==4 else 3 if mode==5 else 0
  if plain in[2,3]and(magic.startswith('HS')or mode in[4,5]):
   if plain==2:pos=2
   else:
    tw,th,radius,field,n=struct.unpack_from('<BBBBH',body);length=struct.unpack_from('<I',body,6)[0];pos=10+length;fields.add(field);entry['observed_vector_field']=field
  if magic=='HD25'and mode in[4,5]:
   grammar=body[pos];grammars.add(grammar);entry['observed_grammar']=grammar;pos+=1
  if magic=='HD25'and(mode in[3,6,7]or(mode in[4,5]and entry['observed_grammar']==1)):
   lo,hi=struct.unpack_from('<II',body,pos);pos+=8
   for length in[lo,hi]:
    end=pos+length
    while pos<end:
     token=body[pos];pos+=1
     if token<128:rles.add('literal');pos+=token+1
     elif token<192:rles.add('zero-run')
     else:rles.add('nonzero-repeat');pos+=1
    assert pos==end
  if magic.startswith('HS'):
   entry['channel_schemes']=[];entry['huffman_tables']=[]
   for c in range(3):
    if magic=='HS33':
     scheme,k,events,size,nb=CH.unpack_from(body,pos);pos+=CH.size;schemes.add(scheme);entry['channel_schemes'].append(scheme);stream=body[pos:pos+size];pos+=size+(nb+7)//8
    else:
     ns,nb=S.unpack_from(body,pos);length=S.size+2*ns+(nb+7)//8;stream=body[pos:pos+length];pos+=length
    if stream:
     ns,nb=S.unpack_from(stream);entry['huffman_tables'].append({'symbols':ns,'coded_bits':nb,'constant':ns==1,'padding_bits':(-nb)%8})
   assert pos==len(body)
  cases.append(entry)
assert modes['HD25']==set(range(10));assert modes['HS32']==modes['HS33']=={0,1,2,3,9,10,11};assert grammars==schemes=={0,1,2};assert rles=={'literal','zero-run','nonzero-repeat'}and fields=={0,1}
record={'status':'PASS_OBSERVED_POSITIVE_PACKET_BRANCHES','cases':cases,'HD25_modes':sorted(modes['HD25']),'HS32_modes':sorted(modes['HS32']),'HS33_modes':sorted(modes['HS33']),'motion_residual_grammars':sorted(grammars),'motion_tile_vector_fields':sorted(fields),'HS33_channel_schemes':sorted(schemes),'HS33_scheme_meanings':{'0':'plain Huffman','1':'zero-run Rice+Huffman','2':'repeat-run Rice+Huffman'},'HD25_byteplane_RLE_tokens':sorted(rles),'no_claim_of_HS33_raw_codec':True,'uncovered':['no Cartesianproduct of every mode and every channel scheme; all requested branches each realized','no exhaustive malformed space; focused18rejects only','no physical SRAM or performance result']};(p/'observed-coverage.json').write_text(json.dumps(record,indent=2)+'\n');print('OBSERVED_MODE_BRANCHES_PASS positive_cases',len(cases))
