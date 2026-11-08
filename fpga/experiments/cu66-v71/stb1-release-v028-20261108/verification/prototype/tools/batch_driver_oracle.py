"""Offline-only ABI3 STB1 batch-driver oracle. No sockets, serial or hardware access."""
import struct,zlib
class Rejected(RuntimeError):pass
class BatchDriver:
    def __init__(self,bus,max_polls=512):self.bus=bus;self.max_polls=max_polls;self.ticket=0
    def identity(self):
        if self.bus.read_words(0,3)!=[0x44593731,0x30000,0x3f] or self.bus.read_words(0x700,2)!=[0x53544231,0x10000]:raise Rejected('explicit ABI3/STB1 identity required')
    def snapshot(self,expected_ticket,prefix,crc):
        for _ in range(self.max_polls):
            flags,credits,stored,actual,ticket,rejected=self.bus.read_words(0x708,6)
            if flags&~0x1f:raise Rejected('unsupported status bits')
            if flags&0x11:raise Rejected('transport/STB1 fault; preserve state')
            # Auto-increment reads are sequential live registers, not atomic snapshots.
            # Drain may finish after the first flags beat; ignore all later busy-sample data.
            if not flags&4 or flags&2:continue
            if flags&8:raise Rejected('contradictory ready/blocked status')
            confirm=self.bus.read_words(0x708,1)[0]
            if confirm&0x11:raise Rejected('fault appeared during snapshot')
            if not confirm&4 or confirm&2:continue
            lo,hi=self.bus.read_words(0x114,2)
            confirmed_ticket=self.bus.read_words(0x718,1)[0]
            if (lo|(hi<<32))!=self.generation or confirmed_ticket!=expected_ticket:raise Rejected('generation/ticket changed around snapshot')
            if (credits,stored,actual,ticket,rejected)!=(256,prefix,crc,expected_ticket,0):raise Rejected('fenced identity/prefix/CRC mismatch')
            return
        raise Rejected('bounded drain wait expired; no retry/reset')
    def stage(self,packet,generation):
        if not 1<=len(packet)<=49152 or not 1<=generation<2**64:raise Rejected('bounded fresh packet required')
        self.identity();self.generation=generation;expected=zlib.crc32(packet);self.bus.begin_packet(generation,len(packet),expected)
        self.snapshot(self.ticket,0,0)
        crc=0
        for offset in range(0,len(packet),1024):
            block=packet[offset:offset+1024]
            if self.ticket==0xffffffff:raise Rejected('ticket exhausted; no wrap/reset')
            self.ticket+=1
            self.bus.write_words(0x720,[generation&0xffffffff,generation>>32,offset,len(block),self.ticket])
            padded=block+b'\xee'*((-len(block))%4)
            self.bus.write_words(0xc00,list(struct.unpack('<'+'I'*(len(padded)//4),padded)))
            crc=zlib.crc32(block,crc);self.snapshot(self.ticket,offset+len(block),crc)
        if self.bus.read_words(0x104,4)!=[len(packet),len(packet),expected,0]:raise Rejected('native written/length/CRC/fault mismatch')
        self.bus.seal_packet(generation,expected)
        return {'bytes':len(packet),'crc32':expected,'descriptors':(len(packet)+1023)//1024,'whole_run_retry':False}
