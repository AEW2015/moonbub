"""Fixed-profile CONST128 descriptor sentinel; sequential lease model only."""
CONSTANT=bytes([128])*64


class ConstantSlots:
    def __init__(self,hidden):
        self.hidden=bytes(hidden);self.count=len(hidden)
        assert all(v in (0,1) for v in hidden)
        self.physical=[[None]*self.count for _ in range(3)]
        self.accepted=self.presented=self.candidate=None;self.written=[]

    def image(self,mapping):
        if mapping is None:return None
        if len(mapping)!=self.count:raise ValueError('descriptor coverage')
        out=[]
        for tile,slot in enumerate(mapping):
            if self.hidden[tile]:
                if slot!=3:raise ValueError('constant profile descriptor')
                out.append(CONSTANT)
            else:
                if slot not in (0,1,2) or self.physical[slot][tile] is None:
                    raise ValueError('invalid physical descriptor')
                out.append(self.physical[slot][tile])
        return out

    def begin(self,tiles,copies,stop_after=None):
        if self.candidate is not None:raise ValueError('candidate active')
        if len(tiles)!=self.count or len(copies)!=self.count:raise ValueError('tile coverage')
        if any(copies) and self.accepted is None:raise ValueError('COPY without reference')
        self.candidate=[];self.written=[]
        for tile,(value,copy) in enumerate(zip(tiles,copies,strict=True)):
            if stop_after is not None and tile==stop_after:break
            if self.hidden[tile]:
                if copy or value!=CONSTANT:raise ValueError('constant profile violation')
                slot=3
            elif copy:
                slot=self.accepted[tile]
                if self.physical[slot][tile]!=value:raise ValueError('false COPY')
            else:
                held=set()
                if self.accepted is not None:held.add(self.accepted[tile])
                if self.presented is not None:held.add(self.presented[tile])
                slot=next(s for s in range(3) if s not in held)
                self.physical[slot][tile]=None;self.physical[slot][tile]=value
                self.written.append((tile,slot))
            self.candidate.append(slot)

    def abort(self):
        if self.candidate is None:raise ValueError('no candidate')
        for tile,slot in self.written:
            assert not self.hidden[tile]
            assert self.accepted is None or self.accepted[tile]!=slot
            assert self.presented is None or self.presented[tile]!=slot
            self.physical[slot][tile]=None
        self.candidate=None;self.written=[]

    def commit(self,expected):
        if self.candidate is None or len(self.candidate)!=self.count:raise ValueError('incomplete candidate')
        if self.image(self.candidate)!=expected:
            self.abort();raise ValueError('content mismatch')
        self.accepted=list(self.candidate);self.candidate=None;self.written=[]

    def present(self):
        if self.accepted is None:raise ValueError('missing accepted')
        self.presented=list(self.accepted)
