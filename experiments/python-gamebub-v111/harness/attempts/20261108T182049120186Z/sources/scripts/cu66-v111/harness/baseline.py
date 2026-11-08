#!/usr/bin/env python3
"""Fresh, bounded emulated-receiver/JPEG RTL baseline; never claim shared time."""
import datetime
import gzip
import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import shutil
import socket
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[3]
AREA = ROOT / 'experiments/python-gamebub-v111/harness'
OLD = ROOT / 'fpga/experiments/throughput30/burst'
EMU = Path('/home/lori/gamebub-tools/esp-emu-study-0510/esp-emu-0.51.0-x86_64-unknown-linux-gnu/esp-emu')
GUEST = Path('/home/lori/gamebub-tools/esp-emu-study-0510/lcd-bypass/live-final-positive')
JPEG = Path('/home/lori/gamebub-tools/esp-emu-study-0510/lcd-bypass/msv1-bridge-multi/src/0000.jpg')
IMAGE = 'gamebub-cu66-v69-tools:20261105'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path, data):
    Path(path).write_text(json.dumps(data, indent=2, sort_keys=True) + '\n')


def memory():
    mem = dict(re.findall(r'^(\w+):\s+(\d+)', Path('/proc/meminfo').read_text(), re.M))
    full = next(x for x in Path('/proc/pressure/memory').read_text().splitlines() if x.startswith('full '))
    return dict(available_bytes=int(mem['MemAvailable']) * 1024,
                psi_full_avg10=float(re.search(r'avg10=([\d.]+)', full)[1]))


def main():
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    out = AREA / 'attempts' / stamp
    build = Path('/home/lori/gamebub-build/cu66-v69') / ('v111-harness-baseline-' + stamp)
    out.mkdir(parents=True)
    build.mkdir()
    (build / 'fixtures').mkdir()
    snapshots = out / 'sources'
    pins = {}
    for line in (OLD / 'live-rtl-bridge/results/rtl-source-sha256-current.txt').read_text().splitlines():
        expected, name = line.split(maxsplit=1)
        assert sha(ROOT / name) == expected, name
        pins[name] = expected
    assert len(pins) == 33
    extra = [OLD / 'live-rtl-bridge/build.sh', OLD / 'esp-emulator-study/live-bridge/run.py',
             OLD / 'esp-emulator-study/live-bridge/adapter.py', OLD / 'esp-emulator-study/live-bridge/check-events.py',
             OLD / 'esp-emulator-study/live-bridge/guest-main.rs', OLD / 'compare-frame.py',
             ROOT / 'firmware/handheld/src/streaming/protocol.rs', Path(__file__).resolve(), Path(__file__).with_name('trace.py')]
    extra += list((ROOT / 'fpga/vendor/core_jpeg/c_model').glob('*'))
    for p in extra:
        if p.is_file():
            pins[str(p.relative_to(ROOT))] = sha(p)
    for name in pins:
        target = snapshots / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / name, target)
    expected_inputs = {'guest.elf':'9018eec674635439907d9ef0b46bb739c04702afcd8cb014f5e2d8bef208cff4',
                       'guest-flash.bin':'873b9c86536dcf19e1bf0a6dad3f182014675b9e232606a6d9bb3b84ee2ec2bd',
                       'fixture.trace':'a8ff3d87e165247637d97fd2b56414f54943337ff7cb11102aa73cba26f26e05'}
    for name, expected in expected_inputs.items():
        assert sha(GUEST / name) == expected
    assert sha(EMU) == '8df332148be34f0271d03d8cebf9f5ef0f67e95cee41e826b5b3f999e9047937'
    assert sha(JPEG) == '8cc99ea7d50d1d20255e41ff7247b0770b3349e705c27152a41817418ce5c9de'
    shutil.copy2(JPEG, build / 'fixtures/0000.jpg')
    shutil.copy2(EMU, build / 'esp-emu')
    for name in expected_inputs:
        shutil.copy2(GUEST / name, build / name)
    image_id = subprocess.check_output(['docker','image','inspect','--format','{{.Id}}',IMAGE], text=True).strip()
    r = dict(schema='v111-emulated-receiver-functional-baseline-v1', status='RUNNING',
             source_sha256=pins, image=IMAGE, image_content_id=image_id,
             external_build=str(build), commands=[], memory_samples=[],
             guest_inputs={str(GUEST/n):h for n,h in expected_inputs.items()}, emulator=dict(path=str(EMU),sha256=sha(EMU)),
             fixture=dict(path=str(JPEG),sha256=sha(JPEG)),
             guest_binary_reused_not_newly_compiled=True, rtl_newly_compiled=False,
             sunshine_executed=False, full_target_application=False,
             guest_kind='receiver-core test application with fixture oracle embedded',
             shared_simulation_time=False, ESP32_cycle_calibrated=False,
             system_fps_qualified=False, hardware_contact=False, actual_run=False,
             limits=['Legacy RTL builder retains -Wno-fatal; compile warnings are recorded, not suppressed as new proof.',
                     'Guest core uses unchanged Rust receiver but bypasses production UI/USB/storage initialization.',
                     'Guest embeds fixture oracle; its SRAM footprint is not a production estimate.',
                     'Actual guest bytes cross a synthetic network and stop-and-wait event bridge to experimental QSPI RTL.',
                     'Blocking DPI socket freezes FPGA time; there is no shared-time or target latency measurement.',
                     'C JPEG oracle shares algorithmic sources; exact match is not independent codec conformance.'])
    write(out/'receipt.json',r)

    def command(argv, name, cap, env=None):
        gate = memory()
        assert gate['available_bytes'] >= 8*1024**3 and gate['psi_full_avg10'] < 1, gate
        container = 'gamebub-v111-harness-' + stamp.lower() + '-' + str(len(r['commands']))
        cmd = ['docker','run','--rm','--init','--name',container,'--memory','8g','--memory-swap','8g',
               '--cpus','2','--pids-limit','2048','--network','none','--ulimit','core=0',
               '--mount',f'type=bind,src={snapshots},dst={snapshots},readonly',
               '--mount',f'type=bind,src={build},dst={build}','-w',str(build)]
        for k,v in (env or {}).items():cmd += ['-e',k+'='+v]
        cmd += [image_id,'timeout','--kill-after=5s',str(cap)+'s',*argv]
        record=dict(argv=cmd,resource_before=gate,timeout_seconds=cap)
        r['commands'].append(record)
        started=time.monotonic()
        with (out/name).open('w') as f:
            p=subprocess.Popen(cmd,stdout=f,stderr=subprocess.STDOUT)
            high=0
            while p.poll() is None:
                sample=dict(command=name,elapsed_seconds=time.monotonic()-started,**memory())
                r['memory_samples'].append(sample)
                high=high+1 if sample['psi_full_avg10']>=5 else 0
                if sample['available_bytes']<4*1024**3 or high>=2 or sample['elapsed_seconds']>cap+20:
                    subprocess.run(['docker','stop','--time','5',container],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=15)
                    record['resource_stop']=sample
                    break
                time.sleep(2)
            record.update(exit_code=p.wait(timeout=20),wall_seconds=time.monotonic()-started)
        write(out/'receipt.json',r)
        assert record['exit_code']==0 and 'resource_stop' not in record,name

    try:
        command([str(build/'esp-emu'),'--version'],'emulator-version.log',30)
        command([str(build/'esp-emu'),'--help'],'emulator-help.log',30)
        command(['verilator','--version'],'verilator-version.log',30)
        command(['g++','--version'],'compiler-version.log',30)
        command(['bash',str(snapshots/'fpga/experiments/throughput30/burst/live-rtl-bridge/build.sh')],
                'rtl-compile.log',900,{'BUILD_DIR':str(build/'rtl')})
        r['rtl_newly_compiled']=True
        command(['g++','-std=c++17','-O2',str(snapshots/'fpga/vendor/core_jpeg/c_model/main.cpp'),'-o',str(build/'cmodel')],
                'cmodel-compile.log',120)
        command(['python3',str(snapshots/'fpga/experiments/throughput30/burst/esp-emulator-study/live-bridge/run.py'),
                 str(build/'live-run'),str(build/'esp-emu'),str(build/'guest.elf'),str(build/'guest-flash.bin'),
                 str(build/'fixture.trace'),str(build/'rtl/obj/Vtb_live_qspi'),str(build/'fixtures')], 'functional-run.log',600)
        for name in ('guest.log','adapter.log','adapter-events.jsonl','rtl.log','event-audit.log','comparison.json'):
            shutil.copy2(build/'live-run'/name,out/name)
        comparison=json.loads((out/'comparison.json').read_text())
        assert comparison['pixels']==comparison['exact_rgb565_pixels']==345600
        assert 'PASS: 28 ordered RTL-acknowledged' in (out/'event-audit.log').read_text()
        r.update(status='PASS_FUNCTIONAL_EMULATED_RECEIVER_JPEG_RTL',actual_run=True,
                 packets=26,payload_bytes=26159,events=28,commits=1,exact_pixels=345600,
                 rtl_binary_sha256=sha(build/'rtl/obj/Vtb_live_qspi'),cmodel_binary_sha256=sha(build/'cmodel'),
                 legacy_compile_warning_count=(out/'rtl-compile.log').read_text().count('%Warning-'),
                 source_unchanged=all(sha(ROOT/n)==h and sha(snapshots/n)==h for n,h in pins.items()))
        assert r['source_unchanged']
        helptext=(out/'emulator-help.log').read_text()
        r['capability_observations']=dict(version='0.51.0',actual_S3_receiver_boot=True,
              actual_guest_network_receiver=True,actual_GP_SPI_DMA_driver=False,
              dedicated_time_step_CLI_found=any(x in helptext for x in ('--run-until','--time-quantum','--step-cycles')),
              gdb_CLI_advertised='--gdb' in helptext,
              controlled_time_API_tested=False,pin_level_QSPI_driver='SV testbench from guest events, not guest GP-SPI registers')
    except Exception as exc:
        r.update(status='FAIL',error=repr(exc))
        raise
    finally:
        r['artifact_sha256']={p.name:sha(p) for p in out.iterdir() if p.is_file() and p.name!='receipt.json'}
        write(out/'receipt.json',r)
        write(AREA/'results.json',dict(schema=r['schema'],status=r['status'],selected_receipt=str((out/'receipt.json').relative_to(ROOT)),
              selected_sha256=sha(out/'receipt.json'),actual_run=r['actual_run'],rtl_newly_compiled=r['rtl_newly_compiled'],
              sunshine_executed=False,shared_simulation_time=False,system_fps_qualified=False,hardware_contact=False))
        print('V111_HARNESS',r['status'],str(out))


if __name__=='__main__':main()
