import copy,struct,unittest,zlib
import decode_stb_failure as d
def fixture(active=1,bound=1,holes=0):
 k,e=2**64-1,2**64-1;attempted=8191;valid=attempted&~holes;flags=1|(2 if valid==8191 else 0)|(8 if holes else 0);x=(holes&-holes).bit_length()-1 if holes else 255;y=2 if holes else 0
 c=dict(a=active,o=2**32-1,f=2**32-1,g=2**64-1,p=255,u=2**64-1,n=2**32-1,i=bound,s=2**64-1 if bound else 0,t=2**64-1 if bound else 0);j=q=2**32-1 if bound else 0
 words=[2**32-1 if valid&(1<<i)else 0 for i in range(13)]
 data=struct.pack('<QQHHBBB',k,e,attempted,valid,flags,x,y)+struct.pack('<BIIQBQIBQQII',c['a'],c['o'],c['f'],c['g'],c['p'],c['u'],c['n'],c['i'],c['s'],c['t'],j,q)+struct.pack('<13I',*words);crc=zlib.crc32(data)
 return[f'STBF1 H k={k} e={e} a={attempted:04x} v={valid:04x} r={flags:02x} x={x} y={y} j={j} q={q} c={crc:08x}',f'STBF1 C k={k} a={c["a"]} o={c["o"]} f={c["f"]} g={c["g"]} p={c["p"]} u={c["u"]} n={c["n"]} i={c["i"]} s={c["s"]} t={c["t"]} c={crc:08x}',f'STBF1 A k={k} c={crc:08x} '+' '.join(f'{v:08x}'for v in words[:7]),f'STBF1 B k={k} c={crc:08x} '+' '.join(f'{v:08x}'for v in words[7:])]
class Tests(unittest.TestCase):
 def test_valid_maximum_and_holes(self):
  for records in(fixture(),fixture(bound=0),fixture(active=0),fixture(holes=1|1<<12)):
   r=d.decode(records);self.assertFalse(r['atomic']);self.assertTrue(all(len(s)<=192 for s in records))
 def test_order_independent_complete_records(self):self.assertEqual(d.decode(fixture()),d.decode(fixture()[::-1]))
 def test_missing_duplicate_extra_rejected(self):
  records=fixture()
  for bad in(records[:3],records+[records[0]],[records[0],records[1],records[2],records[2]]):
   with self.assertRaises(d.Invalid):d.decode(bad)
 def test_every_line_truncation_rejected(self):
  records=fixture()
  for i,line in enumerate(records):
   for n in range(len(line)):
    bad=records.copy();bad[i]=line[:n]
    with self.assertRaises(d.Invalid):d.decode(bad)
 def test_context_and_data_corruption_rejected(self):
  records=fixture()
  for i in range(4):
   for key in(' c=',' k='):
    bad=records.copy();pos=bad[i].index(key)+len(key);bad[i]=bad[i][:pos]+('0'if bad[i][pos]!='0'else'1')+bad[i][pos+1:]
    with self.assertRaises(d.Invalid):d.decode(bad)
  bad=records.copy();bad[1]=bad[1].replace(' p=255',' p=254')
  with self.assertRaises(d.Invalid):d.decode(bad)
 def test_unknown_oversized_or_invalid_grammar(self):
  for line in('STBF1 Z k=0','x'*193,fixture()[0]+' ',fixture()[0].replace(' k=',' k=+'),fixture()[0].replace(' a=1fff',' a=ffff')):
   bad=fixture();bad[0]=line
   with self.assertRaises(d.Invalid):d.decode(bad)
if __name__=='__main__':unittest.main()
