"""Export a frozen v29/v30 (v=1) or v31 (v=2) trace through the existing recorder, never direct serial.

Run only after AV STOP and traffic quiescence. F freezes diagnostic RAM only.
J/K are paginated reads. No arm, reconnect, firmware or FPGA command is sent.
"""
import argparse,json,re,time
from pathlib import Path

PREFIX='USB_TRACE rxdiag v=1 '
PREFIX_PATTERN=re.compile(r'USB_TRACE rxdiag v=([0-9]+) ')
def version(record):return int(record.get('v','1'))
EVENT_FIELDS=[{'us','kind','phase'},{'in_id','in_off','in_v','queued','qv'},
              {'active_id','expected','active_v','since','pv'},
              {'rx','lock','qspi','detail','clipped'},{'consumer','valid'}]
FAILURE_FIELDS=[{'us','in_id','in_off','in_v'},
                {'active_id','expected','active_v','queued','qv','detail'},{'consumer','valid','clipped'},{'rx','tail_ambiguous'}]
def valid_entry(record,fields):
    try:
        if version(record) not in (1,2):return False
        page=int(record['p'])
        if not 0<=page<len(fields):return False
        if not (fields[page]|{'epoch','seq','p'})<=record.keys():return False
        for key,value in record.items():
            if key in {'qv','pv','clipped','valid','tail_ambiguous'}:
                if value not in {'true','false'}:return False
            elif not 0<=int(value)<=2**64-1:return False
        if any(int(record[k])>3 for k in ('in_v','active_v') if k in record):return False
        if 'kind' in record and int(record['kind'])>7:return False
        if 'phase' in record and int(record['phase'])>=16:return False
        return True
    except (KeyError,ValueError):return False
def valid_summary(record,pages):
    try:
        schema=version(record)
        if schema not in (1,2):return False
        page=int(record['s']);phase_count=pages-(9 if schema==1 else 17)
        base=5+phase_count+4
        if not 1<=phase_count<=32 or not 0<=page<pages:return False
        fields=[{'pages','records','failures','armed','frozen','bytes'},
                {'recorded','overwritten','lost_records','lost_phase'},
                {'queue_overflows','lost_failures','failure_overflow','counters_valid','ambiguous_tails'},
                {'first','last','post','triggered','trigger_lost'},{'first_overflow_us','time_valid'}]
        if page<5:required=fields[page]
        elif page<5+phase_count:required={'phase','max_us'}
        elif schema==2 and page>=base:
            required={'kind','lost','loss_valid'}
            if int(record.get('kind','-1'))!=page-base:return False
            if int(record.get('lost','-1'))>2**32-1:return False
        elif record.get('trigger_valid')=='false':required={'trigger_valid'}
        else:required=[{'trigger_valid','seq','us','rx'},
                       {'in_id','in_off','in_v','queued','qv'},
                       {'consumer_id','off','valid','active_id','expected','active_v'},
                       {'phase','since','phase_valid'}][page-5-phase_count]
        if not (required|{'s','epoch'})<=record.keys():return False
        bools={'armed','frozen','counters_valid','triggered','trigger_lost','qv','trigger_valid','phase_valid','time_valid','loss_valid'}
        for key,value in record.items():
            if key in bools:
                if value not in {'true','false'}:return False
            elif not 0<=int(value)<=2**64-1:return False
        if page==0 and (int(record['records'])>96 or int(record['failures'])>32):return False
        return True
    except (KeyError,ValueError,IndexError):return False
def parse_records(text):
    records=[]
    matches=list(PREFIX_PATTERN.finditer(text))
    for i,match in enumerate(matches):
        end=matches[i+1].start() if i+1<len(matches) else len(text)
        part=text[match.end():end].split('\n',1)[0].split(' I (',1)[0]
        values=dict(re.findall(r'\b([a-z_]+)=([A-Za-z0-9_-]+)',part))
        if values:records.append(values|{'v':match.group(1)})
    return records

def validate(summaries,events,failures):
    first=summaries[0];epoch=first['epoch'];schema=version(first)
    assert schema in (1,2),'unsupported schema version'
    assert all(version(x)==schema for x in summaries.values()),'mixed summary schema' 
    assert first['frozen']=='true','trace must be frozen'
    assert first['armed']=='false','trace must be manually sealed'
    assert set(summaries)==set(range(int(first['pages']))),'summary pages missing'
    assert all(x['epoch']==epoch for x in summaries.values()),'summary epoch changed'
    assert all(valid_summary(x,int(first['pages'])) for x in summaries.values()),'invalid summary page'
    if schema==2:
        base=int(first['pages'])-8
        losses=[summaries[i] for i in range(base,base+8)]
        valid=summaries[2]['counters_valid']
        assert all(x['loss_valid']==valid for x in losses),'loss counter validity mismatch'
        assert losses[2]['lost']=='0','Phase is not a salient rejected record'
        if valid=='true':assert sum(int(x['lost']) for x in losses)==int(summaries[1]['lost_records']),'loss totals mismatch'
    for entries,count,pages in [(events,int(first['records']),5),(failures,int(first['failures']),4)]:
        assert set(entries)==set(range(count)),'entry missing'
        for entry in entries.values():
            assert set(entry)==set(range(pages)),'entry page missing'
            assert {x['epoch'] for x in entry.values()}=={epoch},'entry epoch changed'
            assert all(version(x)==schema for x in entry.values()),'mixed entry schema'
            assert len({x['seq'] for x in entry.values()})==1,'torn entry sequence'
            entry_fields=EVENT_FIELDS if pages==5 else FAILURE_FIELDS
            assert all(valid_entry(x,entry_fields) for x in entry.values()),'invalid entry page'
    return True

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--capture',type=Path,required=True)
    ap.add_argument('--output',type=Path,required=True)
    ap.add_argument('--seconds',type=float,default=600)
    args=ap.parse_args()
    if args.output.exists() or not 0<args.seconds<=1200:ap.error('fresh output and <=1200 seconds required')
    capture=json.loads(args.capture.read_text(encoding='utf-8-sig'))
    log=Path(capture['output']);query=Path(capture['query'])
    args.output.mkdir(parents=True)
    offset=log.stat().st_size;deadline=time.monotonic()+args.seconds;pending=''
    summaries={};events={};failures={};observed=[]
    def issue(command):
        while query.exists():
            if time.monotonic()>=deadline:raise TimeoutError('recorder query slot remained occupied')
            time.sleep(.05)
        temporary=query.with_name(query.name+'.export-pending')
        with temporary.open('x',encoding='ascii') as f:f.write(command)
        temporary.rename(query)  # atomic publication; never an empty live query
    def receive(seconds=1.0):
        nonlocal offset,pending
        end=min(deadline,time.monotonic()+seconds);received=[]
        while time.monotonic()<end:
            with log.open('rb') as f:
                f.seek(offset);data=f.read(65536);offset+=len(data)
            if data:
                text=data.decode('utf-8','replace');observed.append(text);pending+=text
                lines=pending.split('\n');pending=lines.pop()
                received+=parse_records('\n'.join(lines)+'\n')
                if received:break
            time.sleep(.04)
        for r in received:
            if 's' in r and 'epoch' in r:
                page_count=int(r.get('pages',summaries.get(0,{}).get('pages','0')))
                if valid_summary(r,page_count):summaries[int(r['s'])]=r
            elif 'e' in r and valid_entry(r,EVENT_FIELDS):events.setdefault(int(r['e']),{})[int(r['p'])]=r
            elif 'f' in r and valid_entry(r,FAILURE_FIELDS):failures.setdefault(int(r['f']),{})[int(r['p'])]=r
        return received
    try:
        sealed=False
        for _ in range(3):
            issue('F');reply=receive(3)
            if any(r.get('result')=='busy' for r in reply):
                raise RuntimeError('receiver is not quiescent; wait for AV STOP')
            if any(r.get('ctrl')=='F' and r.get('ok')=='true' for r in reply):sealed=True;break
        if not sealed:
            raise RuntimeError('freeze not acknowledged; require AV STOP/idle and v29 identity')
        attempts=0
        while time.monotonic()<deadline:
            attempts+=1
            if attempts>160:raise RuntimeError('bounded summary retries exhausted')
            issue('J');receive()
            if 0 in summaries and len(summaries)==int(summaries[0]['pages']):break
        assert 0 in summaries and summaries[0].get('frozen')=='true','no frozen summary'
        assert summaries[0].get('armed')=='false','trace is not manually sealed'
        pages=5*int(summaries[0]['records'])+4*int(summaries[0]['failures'])
        for _ in range(max(1,pages*4)):
            if time.monotonic()>=deadline:raise TimeoutError('bounded export deadline')
            got=sum(len(x) for x in events.values())+sum(len(x) for x in failures.values())
            if got==pages:break
            issue('K');receive()
        validate(summaries,events,failures)
        result=dict(status='COMPLETE_EXPORT',summaries=summaries,events=events,failures=failures,
                    limitation='Export completeness does not erase trace contention, overwrite, clipping or failure-buffer losses; inspect all counters and validity fields.')
    except Exception as exc:
        result=dict(status='INCOMPLETE_EXPORT',error=str(exc),summaries=summaries,events=events,failures=failures)
        raise
    finally:
        (args.output/'export.json').write_text(json.dumps(result,indent=2)+'\n')
        (args.output/'receiver-export.log').write_text(''.join(observed))
        print(result['status'],str(args.output),flush=True)
if __name__=='__main__':main()
