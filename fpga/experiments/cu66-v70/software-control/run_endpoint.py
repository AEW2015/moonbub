#!/usr/bin/env python3
"""Build/qualify the encoded native HUD endpoint and cross-language framing."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
CONTAINER=os.environ.get('TASK_CONTAINER','gamebub-cu66-v69-build')


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    native=ROOT/'experiments/cu66-native-v69'
    files=[*HERE.glob('*.hpp'),*HERE.glob('*.cpp'),*HERE.glob('*.py'),*native.glob('*.hpp'),native/'index.tsv',*sorted((native/'fixtures').glob('*.cu66')),ROOT/'fpga/experiments/cu66-v69/hud-partition/hud_gate.hpp',ROOT/'fpga/experiments/cu66-v70/control-abi/hud_control.py']
    before={str(p.relative_to(ROOT)):sha(p)for p in files};commands=[];runs=[]
    def run(argv,name,timeout=300):
        log=HERE/name
        with log.open('w')as out:r=subprocess.run(argv,cwd=ROOT,stdout=out,stderr=subprocess.STDOUT,timeout=timeout)
        commands.append({'argv':argv,'exit_code':r.returncode,'log':str(log.relative_to(ROOT)),'sha256':sha(log)})
        if r.returncode:raise RuntimeError(f'{name}: exit{r.returncode}; inspect retained log')
        return log.read_text()
    base=['docker','exec',CONTAINER,'g++','-std=c++17','-Wall','-Wextra','-Wconversion','-Werror']
    for sanitized in [False,True]:
        name='sanitized'if sanitized else'release'
        binary='/build/v70-hc70-endpoint'+('-sanitized'if sanitized else'')
        flags=['-O1','-g','-fsanitize=address,undefined','-fno-omit-frame-pointer']if sanitized else['-O2']
        run([*base,*flags,str(HERE/'test_endpoint.cpp'),'-o',binary],f'build-final-{name}.log')
        artifacts='/build/v70-hc70-examples-sanitized'if sanitized else str(HERE/'examples')
        log=run(['docker','exec',CONTAINER,binary,str(native),artifacts],f'test-final-{name}.log')
        assert 'TEST_FAIL'not in log and 'AddressSanitizer'not in log and 'runtime error:'not in log
        row=json.loads(next(s.split('TEST_PASS_ENDPOINT ',1)[1]for s in log.splitlines()if s.startswith('TEST_PASS_ENDPOINT ')))
        assert row['actual_HUD_frames']==457 and row['keys']==20 and row['commands']==2811 and row['malformed_no_state_change']==13 and row['words_transferred_per_actual_frame']==21120
        assert row['commit_retry']and row['abort_retry']and row['old_abort_does_not_discard_new_candidate']
        runs.append({'sanitized':sanitized,**row})
    compat_log=run([sys.executable,'-B',str(HERE/'check_python_compat.py')],'python-compat.log',300)
    assert 'PYTHON_CPP_COMPAT_PASS'in compat_log
    compat=json.loads((HERE/'python-compat-results.json').read_text());assert compat['status']=='PASS'
    assert before=={str(p.relative_to(ROOT)):sha(p)for p in files},'source mutation during qualification'
    examples={str(p.relative_to(ROOT)):sha(p)for p in sorted((HERE/'examples').glob('*.bin'))}
    assert len(examples)==10
    result={'status':'PASS','source_sha256':before,'commands':commands,'runs':runs,'examples_sha256':examples,'python_compat_result_sha256':sha(HERE/'python-compat-results.json'),'limits':{'header_bytes':32,'CRC_trailer_bytes':4,'maximum_payload_bytes':49152,'maximum_complete_frame_bytes':49188,'status_payload_bytes':72,'HUD_words':21120},'scope':'nativeC++encodedHUDendpoint+Pythonframingcompatibility; separatefromtypedpeersystembench','not_proven':['physicaldrain/quiescence','authentication','FPGA/MMIO/transportendpoint','ESP32timingorSRAMfit','fullsystemusesHC70wire']}
    (HERE/'results.json').write_text(json.dumps(result,indent=2)+'\n')
    print('ENCODED_HUD_ENDPOINT_PASS builds=2 frames_per_build=457 encoded_commands_per_build=2811 malformed_no_state_change=13 Python_valid='+str(compat['valid_roundtrip_frames'])+' Python_reject='+str(compat['matching_malformed_rejections'])+' no_old_sources_changed=1')


if __name__=='__main__':main()
