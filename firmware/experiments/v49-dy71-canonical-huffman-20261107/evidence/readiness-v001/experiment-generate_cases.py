from pathlib import Path
import random,struct,json
root=Path('C:/moon/maintenance/v49-canonical-huffman');cases=[];r=random.Random(490107)
def add(name,count,maximum,blob,expected=None):cases.append({'name':name,'count':count,'maximum':maximum,'blob':blob.hex(),'expected':None if expected is None else bytes(expected).hex()})
def pack(pairs,nb,raw=b''):return struct.pack('<HI',len(pairs),nb)+b''.join(bytes(x)for x in pairs)+raw
def encoded(pairs,values):
 code=0;prior=0;lookup={}
 for length,symbol in sorted((n,s)for s,n in pairs):code<<=length-prior;lookup[symbol]=format(code,f'0{length}b');code+=1;prior=length
 bits=''.join(lookup[x]for x in values);nb=len(bits);bits+='0'*(-nb%8);return pack(pairs,nb,int(bits,2).to_bytes(len(bits)//8,'big')if bits else b'')
for symbol in (0,31,255):add('constant'+str(symbol),21120,255,pack([(symbol,1)],0),[symbol]*21120)
for i in range(120):
 ns=r.choice([2,3,4,7,16,32,64,128,256]);depths=[1,1]
 while len(depths)<ns:
  choices=[j for j,n in enumerate(depths)if n<16];j=r.choice(choices);n=depths.pop(j);depths.extend([n+1,n+1])
 r.shuffle(depths);symbols=sorted(r.sample(range(256),ns));pairs=list(zip(symbols,depths));values=symbols+[r.choice(symbols)for _ in range(r.randrange(100,2500))];add('tree'+str(i),len(values),255,encoded(pairs,values),values)
# Explicit full256 and depth16 boundary codebooks.
pairs=[(s,8)for s in range(256)];vals=list(range(256))*4;add('full256',len(vals),255,encoded(pairs,vals),vals)
depths=list(range(1,16))+[16,16];pairs=list(enumerate(depths));vals=list(range(17))*70;add('depth16',len(vals),255,encoded(pairs,vals),vals)
for name,count,maximum,b in [
 ('count0',0,255,pack([(0,1)],0)),('countmax',21121,255,pack([(0,1)],0)),('maximum',3,256,pack([(0,1)],0)),('ns0',3,255,pack([],0)),('ns_gt_count',1,255,pack([(0,1),(1,1)],1,b'\0')),('symbol_gt_max',3,0,pack([(1,1)],0)),('duplicate',3,255,pack([(0,1),(0,1)],3,b'\0')),('decreasing',3,255,pack([(1,1),(0,1)],3,b'\0')),('len0',3,255,pack([(0,0)],0)),('len17',3,255,pack([(0,17)],0)),('constant_len2',3,255,pack([(0,2)],0)),('constant_bits',3,255,pack([(0,1)],1,b'\0')),('oversubscribed',3,255,pack([(0,1),(1,1),(2,1)],3,b'\0')),('incomplete',2,255,pack([(0,2),(1,2)],4,b'\0')),('trailing',2,255,pack([(0,1),(1,1)],3,b'\0')),('bits_truncated',4,255,pack([(0,2),(1,2),(2,2),(3,2)],4,b'\0')),('padding',2,255,pack([(0,1),(1,1)],2,b'\1')),('raw_truncated',8,255,pack([(0,1),(1,1)],8)),('table_truncated',3,255,struct.pack('<HI',2,3)+b'\0\1'),('nb_bound',2,255,pack([(0,1),(1,1)],33,b'\0'*5))]:add(name,count,maximum,b)
for i in range(1000):
 ns=r.randrange(0,15);pairs=[(r.randrange(0,40),r.randrange(0,19))for _ in range(ns)];nb=r.randrange(0,130);blob=pack(pairs,nb,bytes(r.randrange(256)for _ in range((nb+7)//8)));add('random'+str(i),r.randrange(0,40),r.randrange(0,42),blob)
(root/'cases.json').write_text(json.dumps(cases,indent=2)+'\n')
(root/'cases.tsv').write_text(''.join(f"{c['name']}\t{c['count']}\t{c['maximum']}\t{c['blob']}\t{c['expected'] or '-'}\n"for c in cases))
(root/'harness/huffman.cpp').write_text(r'''#include "native/hud.hpp"
#include <fstream>
#include <sstream>
#include <iostream>
#include <iomanip>
#include <chrono>
#include <cassert>
static std::vector<uint8_t> unhex(const std::string&s){std::vector<uint8_t>b;for(size_t i=0;i<s.size();i+=2)b.push_back(uint8_t(std::stoul(s.substr(i,2),nullptr,16)));return b;}
int main(int argc,char**argv){assert(argc==2);std::ifstream f(argv[1]);assert(f);std::string line;
 while(std::getline(f,line)){std::istringstream row(line);std::string name,hex,expected;unsigned count,max;row>>name>>count>>max>>hex>>expected;assert(row);auto b=unhex(hex);cu66_port::Arena arena(98304);std::string result;
  {cu66_port::Scope scope(arena);try{cu66::Reader reader({b.data(),b.size()});auto out=cu66::huffman(reader,count,max);reader.end();std::ostringstream text;text<<"OK:";for(auto x:out)text<<std::hex<<std::setw(2)<<std::setfill('0')<<unsigned(x);result=text.str();if(expected!="-")assert(result=="OK:"+expected);}catch(const std::exception&e){result="ERR:"+std::string(e.what());if(expected!="-"){std::cerr<<name<<" unexpectedlyfailed "<<result<<"\n";return 3;}}}
  assert(arena.live==0);std::cout<<name<<"\t"<<result<<"\t"<<arena.peak<<"\t"<<arena.allocations<<"\n";
 }
}''')
print('cases',len(cases))
