from pathlib import Path
import re

def split_top(s):
 out=[];start=0;depth=0
 for i,c in enumerate(s):
  if c in '([{':depth+=1
  elif c in ')]}':depth-=1
  elif c==','and depth==0:out.append(s[start:i].strip());start=i+1
 out.append(s[start:].strip());return out

def close(s,start):
 depth=0
 for i in range(start,len(s)):
  if s[i]=='(':depth+=1
  elif s[i]==')':
   depth-=1
   if depth==0:return i
 raise ValueError('unclosed')

def ports(text):
 m=re.search(r'\bmodule\s+\w+',text);pos=m.end()
 while text[pos].isspace():pos+=1
 if text[pos]=='#':pos=close(text,text.index('(',pos))+1
 op=text.index('(',pos);end=close(text,op);result=[];direction=None;width=''
 for token in split_top(text[op+1:end]):
  token=' '.join(token.split());m=re.fullmatch(r'(input|output)\s+(?:(?:logic|wire|reg)\s+)?(\[[^]]+\])?\s*(\w+)(?:\s*(\[[^]]+\]))?',token)
  if m:direction,width,name,array=m.groups();width=width or '';array=array or ''
  else:
   m=re.fullmatch(r'(\w+)(?:\s*(\[[^]]+\]))?',token);assert m,token;name,array=m.groups();array=array or ''
  result.append(dict(direction=direction,width=width,name=name,array=array))
 return op,end,result

def abstract(text,modname,children):
 op,end,original_ports=ports(text);fports=[];removed=[]
 for module,instance,path in children:
  marker=module+' '+instance+'(';start=text.index(marker);begin=text.index('(',start);stop=close(text,begin);finish=text.index(';',stop)+1
  defs={x['name']:x for x in ports(Path(path).read_text())[2]};assignments=[]
  for tok in split_top(text[begin+1:stop]):
   m=re.fullmatch(r'\.(\w+)(?:\((.*)\))?',tok,re.S);assert m,tok;port,arg=m.groups();arg=port if arg is None else arg.strip()
   if defs[port]['direction']!='output'or not arg:continue
   assert re.fullmatch(r'\w+',arg),(port,arg)
   pd=defs[port];indices=[None]
   if pd['array']:
    a,b=map(int,re.findall(r'\d+',pd['array']));indices=list(range(min(a,b),max(a,b)+1))
   for index in indices:
    name='f_'+arg+(''if index is None else'_'+str(index));target=arg+(''if index is None else'['+str(index)+']');assert name not in[x['name']for x in fports]
    fports.append(dict(name=name,width=pd['width'],array='',direction='input',child_module=module,child_instance=instance,child_port=port,target=target));assignments.append('    assign '+target+'='+name+';')
  removed.append(dict(module=module,instance=instance,exact_instance_text=text[start:finish]))
  text=text[:start]+'\n'.join(assignments)+text[finish:]
 op,end,_=ports(text);text=text[:end]+',\n'+',\n'.join('    input wire '+x['width']+' '+x['name']for x in fports)+',\n    output wire formal_violation\n'+text[end:]
 text=re.sub(r'\bmodule\s+\w+','module '+modname,text,count=1)
 pos=text.rindex('endmodule');text=text[:pos]+'''    reg formal_reset_seen=0;
    always_ff @(posedge clk)if(rst)formal_reset_seen<=1;
    assign formal_violation=formal_reset_seen&&((state==PARSER_START||state==METADATA)&&hud_requested);
'''+text[pos:]
 return text,original_ports,fports,removed
