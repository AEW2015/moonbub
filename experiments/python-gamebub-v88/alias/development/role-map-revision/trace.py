"""Addressed alias traffic and explicit descriptor-storage sensitivity.

Pixel data uses three slots per canonical tile. BL8 transfers are 16 bytes.
Descriptor maps have 8100 two-bit entries; padded map stride is 2048 bytes.
"""
from collections import Counter
import hashlib
import json

TILES=8100
PIXELS=518400
MAP_BYTES=2025
MAP_STRIDE=2048
MAP_BASE=3*PIXELS
HUD_BASE=MAP_BASE+3*MAP_STRIDE
CONTROL_BASE=HUD_BASE+42240


def tile_address(slot,tile):
    assert 0<=slot<3 and 0<=tile<TILES
    return slot*PIXELS+tile*64


def descriptor(map_slot,tile):
    return MAP_BASE+map_slot*MAP_STRIDE+tile//4,(tile%4)*2


def commands(frame,old,new,presented,dirty,*,candidate_map=2):
    """Logical descriptor accesses and actual aligned 16-byte data commands.

    Map IDs0/1/2 here are logical accepted/presented/candidate roles, not reused
    physical descriptor banks; publication is a modeled atomic role exchange.
    """
    events=[]
    def emit(kind,direction,address,bl8=0,**fields):
        events.append(dict(kind=kind,direction=direction,address=address,BL8=bl8,**fields))
    for word in range((MAP_BYTES+15)//16):
        emit('descriptor_clear','write',MAP_BASE+candidate_map*MAP_STRIDE+word*16,entries=min(64,TILES-word*64),map=candidate_map)
    for tile in range(TILES):
        if old is not None:
            a,b=descriptor(0,tile);emit('descriptor_accepted','read',a,tile=tile,bit_offset=b,map=0)
        if presented is not None:
            a,b=descriptor(1,tile);emit('descriptor_presented','read',a,tile=tile,bit_offset=b,map=1)
        if not frame['key'] and not frame['hidden_mask'][tile] and (not frame['copy_ref_mask'][tile] or tile in dirty):
            for beat in range(4):emit('reference_read','read',tile_address(old[tile],tile)+beat*16,1,tile=tile,slot=old[tile])
        if not frame['copy_ref_mask'][tile]:
            for beat in range(4):emit('canonical_write','write',tile_address(new[tile],tile)+beat*16,1,tile=tile,slot=new[tile])
        a,b=descriptor(candidate_map,tile);emit('descriptor_candidate','write',a,tile=tile,bit_offset=b,map=candidate_map)
    for beat in range(2640):emit('HUD_write','write',HUD_BASE+beat*16,1)
    for beat in range(2640):emit('HUD_read','read',HUD_BASE+beat*16,1)
    emit('publication','control',CONTROL_BASE,0,cycles=2)
    for tile in range(TILES):
        a,b=descriptor(candidate_map,tile);emit('descriptor_scanout','read',a,tile=tile,bit_offset=b,map=candidate_map)
        for beat in range(4):emit('scanout_read','read',tile_address(new[tile],tile)+beat*16,1,tile=tile,slot=new[tile])
    return events


def account(events,policy):
    """Count addressed transactions; logical on-chip accesses are separate.

    cached: independent one-word accepted/presented/scanout caches; complete
    candidate words accumulated then overwritten, with known INVALID padding.
    uncached: every entry lookup reads a word; entry writes do external RMW.
    onchip: dedicated one-entry/cycle nominal map read/write resources.
    """
    assert policy in ('onchip','cached','uncached')
    counts=Counter({name:0 for name in ('reference_read_BL8','canonical_write_BL8','HUD_read_BL8','HUD_write_BL8','scanout_read_BL8','descriptor_read_BL8','descriptor_write_BL8','descriptor_read_cycles','descriptor_write_cycles')});last={};candidate_words=set()
    for event in events:
        kind=event['kind'];direction=event['direction'];n=event['BL8']
        if n:
            assert n==1 and event['address']%16==0
            counts[kind+'_BL8']+=1
            counts['data_'+direction+'_BL8']+=1
        elif kind=='publication':counts['publication_cycles']+=event['cycles']
        else:
            counts[kind+'_logical_entries']+=event.get('entries',1)
            if policy=='onchip':
                counts['descriptor_'+direction+'_cycles']+=event.get('entries',1)
            else:
                word=event['address']//16*16
                if kind=='descriptor_clear':counts['descriptor_write_BL8']+=1
                elif kind=='descriptor_candidate':
                    if policy=='uncached':
                        counts['descriptor_read_BL8']+=1;counts['descriptor_write_BL8']+=1
                    else:candidate_words.add(word)
                elif policy=='uncached' or last.get(kind)!=word:
                    counts['descriptor_read_BL8']+=1;last[kind]=word
    if policy=='cached':counts['descriptor_write_BL8']+=len(candidate_words)
    reads=counts['data_read_BL8']+counts['descriptor_read_BL8']
    writes=counts['data_write_BL8']+counts['descriptor_write_BL8']
    counts['total_read_BL8']=reads;counts['total_write_BL8']=writes
    counts['memory_busy_cycles']=reads*18+writes*16
    counts['decoder_data_read_BL8']=counts['data_read_BL8']-counts['scanout_read_BL8']
    counts['decoder_memory_busy_cycles']=(reads-counts['scanout_read_BL8'])*18+writes*16
    return dict(sorted(counts.items()))


def digest(events):
    return hashlib.sha256(json.dumps(events,sort_keys=True,separators=(',',':')).encode()).hexdigest()
