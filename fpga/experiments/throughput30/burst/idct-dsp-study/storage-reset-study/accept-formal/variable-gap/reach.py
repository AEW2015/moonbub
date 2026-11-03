#!/usr/bin/env python3
"""Exhaustive reachable control states; see README for contract and state map."""
from collections import deque
import argparse

def choices(i,g):
 if g: return [(False,i,g-1)]
 if i==0: return [(False,i,0),(True,1,0)]
 if i==63:return [(True,0,GAP)]
 return [(True,i+1,0)]

def advance(s,v,ni,ng):
 i,g,flags,wr,rd,ri,st=s
 accept=not (flags>>wr)&1
 if v and i==63 and accept: flags|=1<<wr;wr^=1
 if st==2 and ri==63:flags&=~(1<<rd);rd^=1
 if st==0:
  # read old flags; reconstruct from original state, before writes
  ns=1 if ((s[2]>>s[4])&1) else 0
 elif st==1:ns=2
 elif st==2:ns=0 if ri==63 else 2
 else:ns=st
 if st==2:ri=(ri+1)&63
 return (ni,ng,flags,wr,rd,ri,ns)

def run(gap):
 global GAP;GAP=gap
 start=(0,0,0,0,0,0,0);seen={start:None};q=deque([start]);edges=0
 while q:
  s=q.popleft()
  for v,ni,ng in choices(s[0],s[1]):
   edges+=1
   if v and ((s[2]>>s[3])&1):
    path=[];p=s
    while seen[p] is not None:
     prev,decision=seen[p];path.append(int(decision));p=prev
    path.reverse();path.append(1)
    print(f'REJECT gap={gap} states={len(seen)} edges={edges} transition={len(path)} state={s} path={"".join(map(str,path))}')
    return False
   ns=advance(s,v,ni,ng)
   if ns not in seen:seen[ns]=(s,v);q.append(ns)
 for s in seen:
  for v,ni,ng in choices(s[0],s[1]):
   if v and ((s[2]>>s[3])&1): raise AssertionError('closure has reject')
   if advance(s,v,ni,ng) not in seen: raise AssertionError('not closed')
 print(f'REACH_PASS gap={gap} states={len(seen)} edges={edges} closure=checked')
 return True
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--gap',type=int,default=2);a=p.parse_args()
 if not 0<=a.gap<=3:raise SystemExit('gap range 0..3')
 raise SystemExit(0 if run(a.gap) else 1)
