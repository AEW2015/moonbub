#!/usr/bin/env python3
from pathlib import Path
import hashlib,json
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 r=json.loads((HERE/'results.json').read_text());inventory=json.loads((HERE/'native-hud-audit.json').read_text())
 for rel,digest in r['source_sha256'].items():assert sha(HERE/rel)==digest,rel
 for rel,digest in inventory['source_sha256'].items():assert sha(ROOT/rel)==digest,rel
 log=(HERE/'regression.log').read_text();assert 'TEST_FAIL'not in log and'AddressSanitizer'not in log and'runtime error:'not in log
 runs=[json.loads(line.split('TEST_PASS ',1)[1])for line in log.splitlines()if line.startswith('TEST_PASS ')];assert len(runs)==2
 for run in runs:
  assert run['frames']==457 and run['keys']==20 and run['logical_words_per_cache']==21120 and run['logical_bytes_per_cache']==42240 and run['maximum_one_cache_word_capacity_bytes']==47616 and run['maximum_previous_plus_candidate_word_capacity_bytes']==94720 and run['HUD_decode_rejections']==2 and run['base_failed_valid_HUD_rollbacks']==4 and run['software_endpoint_is_Linux_host']and not run['physical_DMA_or_FPGA_HUD_decoder_proven']
 directed=[json.loads(line)for line in log.splitlines()if line.startswith('{')];assert directed[-1]['native_directed_HUD_cases']==32
 assert runs==r['runs'];assert inventory['frames']==457 and inventory['exact_patches']==1828 and inventory['envelopes']=={'HX33':443,'HU25':14};assert inventory['hypothetical_all_raw_HU25']['frames_exceeding_49152']==279
 contract=json.loads((HERE/'interface-contract.json').read_text());assert [(x['value'],x['name'])for x in contract['opcodes']]==list(enumerate(('PREPARE','STATUS','READ_CANDIDATE','ACK_EXTERNAL_WRITE_DRAIN','COMMIT','ABORT','RESET'),1));assert not contract['full_CU66_FPGA_decoder']and not contract['wire_or_MMIO_encoding_implemented']
 print(json.dumps(dict(full_HUD_frames_per_build=457,release_and_sanitized_gate_runs=2,native_HUD_directed_cases=32,previous_HUD_immutable=True,base_failed_after_transfer_rollbacks=4,software_endpoint='Linux native C++',processor_SRAM_or_physical_DMA_proven=False,source_pins=len(r['source_sha256']))))
if __name__=='__main__':main()
