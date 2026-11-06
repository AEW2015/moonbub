import re,fnmatch

def parse(root,native):
 pins={};standards={}
 for f in root.glob('*.xdc'):
  text=f.read_text()
  for m in re.finditer(r'set_property\s+-dict\s+\{([^}]+)\}\s*\[get_ports\s+(?:\{([^}]+)\}|([^\]]+))\]',text):
   a=m[1].split();v=dict(zip(a[::2],a[1::2]));name=(m[2]or m[3]).strip()
   if'PACKAGE_PIN'in v:pins[name]=v['PACKAGE_PIN']
   if'IOSTANDARD'in v:standards[name]=v['IOSTANDARD']
  for m in re.finditer(r'set_property\s+(PACKAGE_PIN|IOSTANDARD)\s+(\S+)\s+\[get_ports\s+(?:\{([^}]+)\}|([^\]]+))\]',text):
   for name in(m[3]or m[4]).split():
    if m[1]=='PACKAGE_PIN':pins[name]=m[2]
    else:
     for p in native:
      if p==name or(name.endswith('[*]')and p.startswith(name[:-3]+'[')and re.search(r'\[\d+\]$',p))or('['not in name and fnmatch.fnmatchcase(p,name)):standards[p]=m[2]
 return pins,standards
