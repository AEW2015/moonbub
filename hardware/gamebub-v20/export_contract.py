#!/usr/bin/env python3
"""Generate byte offsets and replayable FG19 control vectors from frozen code."""
import hashlib,importlib.util,json,struct,sys,zlib
from pathlib import Path
import reference as ref
HERE=Path(__file__).resolve().parent;ROOT=ref.ROOT

def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m);return m
FGDIR=ROOT/'experiments/python-game-frame-grant-study'
framing=load('v20_abi_framing',FGDIR/'framing.py');fc=load('v20_abi_frame_credit',FGDIR/'frame_credit.py')
old=sys.modules.get('framing');sys.modules['framing']=framing
try:gateway=load('v20_abi_gateway',FGDIR/'gateway.py')
finally:
    if old is None:sys.modules.pop('framing',None)
    else:sys.modules['framing']=old

def layout(endian,fields,fmt,crc):
    values=[];offset=0
    for name,kind in fields:
        n=struct.calcsize(endian+kind);values.append(dict(name=name,offset=offset,bytes=n,format=kind));offset+=n
    assert endian+''.join(k for _,k in fields)==fmt.format
    assert offset==fmt.size
    return dict(endianness='little' if endian=='<' else 'big',fields=values,field_bytes=offset,
        trailer_crc_bytes=4 if crc else 0,total_header_or_message_bytes=offset+(4 if crc else 0),
        crc_definition=None if not crc else 'IEEE/zlib CRC32 of preceding message/body bytes, stored in declared endianness')
def build():
    profiles={
      'AR03':layout('<',list(zip(('magic','version','flags','epoch','frame','reference_bank','destination_bank','reference_id','reference_tag','stored_tag','inner_bytes','patch_count','patch_blob_bytes'),('4s','B','B','I','I','B','B','I','16s','16s','I','B','I'))),ref.stripe.trace.codec.HEADER,True),
      'AF03':layout('<',list(zip(('magic','version','status','epoch','frame','body_crc','stored_bank','stored_id','stored_tag'),('4s','B','B','I','I','I','B','I','16s'))),ref.stripe.trace.codec.FEEDBACK,True),
      'GF03':layout('!',list(zip(('magic','version','epoch','frame','total_bytes','fragment_index','fragment_count','payload_bytes','complete_packet_crc','ar03_body_crc'),('4s','B','I','I','I','H','H','H','I','I'))),framing.HEADER,False),
      'TOKEN':layout('!',list(zip(('epoch','packet_slot','reserved_zero','sequence'),('I','H','H','Q'))),gateway.TOKEN,False),
      'PC18':layout('!',list(zip(('magic','epoch','packet_slot','query_reply_flag','sequence','status','token_header_crc'),('4s','I','H','H','Q','B','I'))),gateway.REPLY,True),
      'QC18':layout('!',list(zip(('magic','epoch','packet_slot','reserved_zero','sequence','token_header_crc'),('4s','I','H','H','Q','I'))),gateway.QUERY,True),
      'FG19':layout('!',list(zip(('magic','version','kind','frame_slot','epoch','frame','nonce','total_bytes','ar03_body_crc'),('4s','B','B','H','I','I','Q','I','I'))),fc.FMT,True)}
    profiles['AR03'].update(header_bytes=ref.stripe.trace.codec.HEADER.size,fixed_envelope_bytes=ref.stripe.trace.codec.HEADER.size+4,variable_body='inner GM01/SR01 bytes then length-prefixed UI patch blob',trailer_position='CRC32 is the final four packet bytes after variable body, NOT immediately after header')
    rows=json.loads((FGDIR/'results.json').read_text());control=[]
    for case in rows['cases']:
        grants=case['result']['frame_grants']
        if grants is None:continue
        events=[]
        for event in grants['history']:
            if event['event'] not in ('sender_request','sender_cancel','sender_finish','receiver_reply'):continue
            wire=fc.seal(event['kind'],event['slot'],event['frame'],event['seq'],event['total'],event['crc']);parsed=fc.parse(wire)
            assert parsed['frame']==event['frame'] and parsed['seq']==event['seq']
            events.append(dict(event=event['event'],wire_hex=wire.hex(),wire_sha256=hashlib.sha256(wire).hexdigest(),parsed=parsed,
                original_model_at_ms=event['at_ms'],delivered=event.get('delivered',True)))
        control.append(dict(profile=case['profile'],events=events,safe_stop=grants['safe_stop'],safe_stop_reason=grants['safe_stop_reason']))
    # One actual AR03 -> GF03 first fragment and packet-credit exchange.
    desc=json.loads((ref.fixture.TRACE/'results.json').read_text())['cohorts'][0]['rows'][0]
    rgb=ref.stripe.fixture.array(desc['source_rgb888'])
    selector=ref.stripe.trace.codec._ui().PatchSelector(rectangles=((22,54,160,24),(22,82,160,24),(168,360,320,24),(168,390,240,24)))
    enc=ref.stripe.trace.codec.Encoder(epoch=1,mode='gm',patch_builder=selector)
    decision=enc.prepare(rgb,0,quant_scale=16);assert decision.accepted
    packet=decision.packet;meta=ref.stripe.trace.codec.identity(packet)
    rx=ref.stripe.trace.codec.Receiver();task=rx.begin(packet);display,info,ack=rx.complete(task)
    assert enc.ack(ack)
    fragment=framing.datagrams(packet,meta['epoch'],meta['frame_id'])[0]
    wrapped=gateway.TOKEN.pack(1,0,0,1)+fragment;decoded=gateway.unwrap(wrapped)
    pc=gateway.seal(gateway.REPLY.pack(b'PC18',1,0,0,1,0,decoded['crc']))
    qc=gateway.seal(gateway.QUERY.pack(b'QC18',1,0,0,1,decoded['crc']))
    return dict(schema='gamebub-v20-lab-wire-contract-v1',layouts=profiles,
        limits=dict(coded_width=720,coded_height=480,active_width=720,active_height=405,source_schedule_fps=30,complete_frame_cap=49152,
            gf_payload_bytes=framing.PAYLOAD,max_data_udp_bytes=1055,esp_dma_allocation_bytes=1065,mailbox_entries=6,data_tokens=5,frame_slots=2,
            sender_transactions=3,framebuffers=3,control_outstanding=1,epoch_lab_value=1),
        values=dict(no_bank=255,no_frame=4294967295,frame_control={name:getattr(fc,name) for name in ('REQUEST','CANCEL','GRANT','BUSY','RELEASE','CANCELED','FINISH','FINISHED')},ar03_key=1,ar03_promote=2,af03_ack=1,af03_nack=2),
        packet_example=dict(origin='Actual epoch1 AR03 key encoded from retained native source RGB and decoded through frozen AR03 receiver',ar03_packet_hex=packet.hex(),decoded_display_sha256=hashlib.sha256(display.tobytes()).hexdigest(),ar03_sha256=hashlib.sha256(packet).hexdigest(),ar03_header_hex=packet[:ref.stripe.trace.codec.HEADER.size].hex(),
            wrapped_first_gf03_hex=wrapped.hex(),pc18_hex=pc.hex(),qc18_hex=qc.hex(),af03_hex=ack.hex()),
        frame_control_sequences=control,
        publication_rules=['GRANT reserves exact frame capacity; it does not consume AR03 identity or publish a YUV bank.',
            'PC18 permits only packet-buffer reuse. FINISHED confirms the drain barrier, not frame-slot release.',
            'RELEASE follows ingress/read/decode drain. AF03 alone confirms decoded reference publication.',
            'CRC/body/epoch/frame/bank/tag checks and expected canonical tag must succeed before atomic publication.',
            'Old/wrong-kind/wrong-slot replies cannot release a different owner. Unknown outcomes retain bounded ownership and stop.',
            'Display-only exact RGB565 patches never modify prediction banks or canonical reference tags.'],
        gaps=['Lab epoch1 only; production profile negotiation/reset/rekey and unknown-outcome recovery are not implemented.',
            'MSV1 JPEG firmware does not implement AR03/GF03/FG19; gate new endpoints behind explicit capability negotiation.',
            'No RTL decoder, fitted resource/Fmax, physical scanline proof, ESP ISA/RF calibration or sustained hardware30fps supplied.'])
def header(d):
    lines=['/* Generated by export_contract.py; byte offsets, never cast packed C structs. */','#ifndef GB_V20_WIRE_H','#define GB_V20_WIRE_H']
    for name,desc in d['layouts'].items():
        lines.append(f'#define GB_V20_{name}_FIELD_BYTES {desc["field_bytes"]}u')
        for field in desc['fields']:lines.append(f'#define GB_V20_{name}_{field["name"].upper()}_OFFSET {field["offset"]}u')
    for name,value in d['values']['frame_control'].items():lines.append(f'#define GB_V20_FG19_{name} {value}u')
    lines+=['#define GB_V20_COMPLETE_CAP 49152u','#define GB_V20_GF_PAYLOAD 1008u','#endif']
    return '\n'.join(lines)+'\n'
def main():
    d=build();(HERE/'wire-contract.json').write_text(json.dumps(d,indent=2)+'\n')
    (HERE/'include/gb_wire.h').write_text(header(d));print('exported wire layouts and',sum(len(c['events']) for c in d['frame_control_sequences']),'FG19 messages')
if __name__=='__main__':main()
