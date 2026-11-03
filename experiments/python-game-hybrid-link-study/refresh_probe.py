#!/usr/bin/env python3
"""Separate initial-key-only probe; baseline refresh results stay unchanged."""
import json
import os
from pathlib import Path
import benchmark as b

HERE=Path(__file__).resolve().parent


def main():
    paths=[HERE/'refresh_probe.py',HERE/'benchmark.py',HERE/'model.py',HERE/'adapter.py']
    pins={str(p):b.sha(p) for p in paths};cases=[]
    media=Path(os.environ.get('GAMEBUB_MEDIA_DIR',str(HERE.parents[3]/'media')))
    for clip in ('mass-effect-combat','mass-effect-2600'):
        frames,manifest=b.source.native(media/(clip+'.mp4'))
        c=b.run_case(frames,manifest,clip,512,288,30,'adaptive_ui','initial_key_only_probe',refresh_period=0)
        assert [p['id'] for p in c['result']['packets'] if p.get('key')]==[0]
        cases.append(c);r=c['result']
        print(clip,r['presented_strict'],r['presented_eventual'],r['metrics']['steady_fps'],r['drops_by_reason'],flush=True)
    assert pins=={str(p):b.sha(p) for p in paths}
    result={'evidence':'Separate initial-key-only finiteHG01probe, notdefaultpolicyorlongduration30fpsproof',
        'source_sha256':pins,'cases':cases,
        'scope':'Same60nativeframeIDs replayedat30; periodicrefreshdisabled onlyforthis2sprobe. Baseline29diagnosticresultsremainunchanged. Codecservicesremeasured,sodifferencescanincludehosttiming. Noheldoutscenecut/recovery/longmotionqualification. Akey-onlypolicycanleaveoldpredictionreferencesandworsencaps/quality; notselectedforproduction.'}
    (HERE/'refresh-results.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')


if __name__=='__main__':main()
