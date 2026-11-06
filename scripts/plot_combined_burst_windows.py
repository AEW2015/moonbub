"""Plot physical BL8 error counts; source tables remain the authoritative records."""
from pathlib import Path
import csv,json,sys
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
r=Path(__file__).resolve().parents[1]
w=Path(sys.argv[1]) if len(sys.argv)>1 else Path(json.loads((r/'evidence/current-combined-window.json').read_text())['window'])
tables=[('phase-slot-summary.tsv','actual_phase_mdeg','Programmed read phase (degrees)',1000),('tap-slot-summary.tsv','tap','Common IDELAY tap',1)]
fig,axes=plt.subplots(2,1,figsize=(12,6.7),layout='constrained')
for ax,(name,key,label,scale)in zip(axes,tables):
 rows=list(csv.DictReader((w/name).open(),delimiter='\t'));xs=sorted({int(x[key])for x in rows})
 assert len(rows)==4*len(xs),('incomplete table',name,len(rows))
 counts=np.zeros((4,len(xs)),dtype=np.int64);passed=np.zeros_like(counts)
 for x in rows:
  i=xs.index(int(x[key]));s=int(x['slot']);counts[s,i]=int(x['errors']);passed[s,i]=int(x['pass'])
 image=ax.imshow(np.log10(counts+1),origin='lower',aspect='auto',cmap='RdYlGn_r',vmin=0,vmax=6,
  extent=[-0.5,len(xs)-0.5,-0.5,3.5])
 for s,i in zip(*np.where(passed==1)):ax.plot(i,s,'o',ms=3,color='black')
 ticks=list(range(0,len(xs),max(1,len(xs)//12)))
 if len(xs)-1 not in ticks:ticks.append(len(xs)-1)
 ax.set_xticks(ticks,[f'{xs[i]/scale:g}'for i in ticks]);ax.set_yticks(range(4))
 ax.set_xlabel(label);ax.set_ylabel('Capture slot');ax.set_title('Phase sweep, tap 0'if key!='tap'else'Tap sweep, read phase 90°')
fig.colorbar(image,ax=axes,label='log10(mismatched words + 1)',shrink=0.8)
fig.suptitle('Physical SERDES4 BL8 window checks — 166.015625 MHz\n65,536 words × 9 patterns per point; capture delay 3; fixed transmit timing\nBlack dots: zero-error complete PASS. Not an independent transmit-eye measurement.',fontsize=11)
for suffix in ['png','svg']:fig.savefig(w/f'burst-read-windows.{suffix}',dpi=180)
plt.close(fig);print(w/'burst-read-windows.png')
