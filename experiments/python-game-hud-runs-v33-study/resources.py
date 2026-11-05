#!/usr/bin/env python3
"""Declared logical decoder layout and observed selected-stream statistics."""
from pathlib import Path
from collections import Counter
import hashlib,json
HERE=Path(__file__).resolve().parent
def main():
 data=json.loads((HERE/'results.json').read_text());schemes=Counter();modes=Counter();maxsymbols=maxbits=0;rows=[];trial_schemes=trial_k=0
 for case in data['cases']:
  for row in case['rows']:
   coded=rice=events=0
   for patch in row['work']['patches']:
    for trial in patch['trials']:
     for channel in trial['channels']:
      trial_schemes+=len(channel['trials']);trial_k+=sum(t.get('rice_k_trials',0) for t in channel['trials'])
    if patch['selected_kind']!=4:continue
    modes[patch['selected_mode']]+=1
    for channel in patch['selected_channels']:
     s=channel['selected'];schemes[s['scheme']]+=1;coded+=s['huffman']['coded_bits'];rice+=s['rice_bits'];events+=s['events']
     maxsymbols=max(maxsymbols,s['huffman']['symbols']);maxbits=max(maxbits,s['huffman']['maximum_code_bits'])
   rows.append(dict(scene=case['scene'],id=row['id'],huffman_coded_bits=coded,rice_bits=rice,symbol_events=events))
 # Exhaustive geometry bound, including the thin/fringe-dominated cases.
 max_tiles,w,h=max((((w+15)//16)*((h+7)//8),w,h) for w in range(1,721) for h in range(1,481) if w*h<=21120)
 layout=dict(canonical_table_symbol_bytes=253,canonical_table_16_firstcode_count_firstindex_bytes=16*8,
  full_geometry_motion_vectors_bytes=2*max_tiles,header_buffers_outer106_patch46_channel14_huffman6_bytes=172,
  input_cursor_four_u32_bytes=16,huffman_work_four_u32_bytes=16,run_work_eight_u32_bytes=32,
  component_work_four_i32_bytes=16,control_sixteen_u32_bytes=64,sha256_serial_workspace_bytes=144,
  outer_and_patch_reference_and_output_tags_bytes=64,outer_and_patch_crc32_bytes=8)
 logical=sum(layout.values())
 output=dict(schema='gamebub-run-HUD-v33-resources',selected_channel_schemes=dict(schemes),selected_patch_modes=dict(modes),
  observed_max_huffman_symbols=maxsymbols,observed_max_huffman_code_bits=maxbits,paid_channel_scheme_trials=trial_schemes,paid_rice_k_size_trials=trial_k,
  rows=rows,declared_HS33_logical_layout_bytes=layout,declared_HS33_logical_state_total_bytes=logical,
  fallback_palette512_usedbitmap32_replaces_canonical381_bytes=544,
  declared_all_four_patch_kinds_logical_state_total_bytes=logical-381+544,
  maximum_tile_count_geometry=dict(tiles=max_tiles,width=w,height=h,domain='1<=w<=720,1<=h<=480,w*h<=21120'),
  canonical_depth_bound=16,canonical_alphabet_bound=253,rice_k_bound=14,channel_output_word_bound=21120,
  conservative_new_frame_bit_read_bound=3*21120*16+3*(16*21120+1),
  external_reference_HUD_bytes=42240,external_staging_HUD_bytes=42240,external_reference_plus_stage_HUD_bytes=84480,
  external_seekable_packet_max_bytes=49152,reference_stage_and_one_complete_packet_bytes=133632,
  parser_wide_max_HUD_words_with_legacy_full_patches=720*480,parser_wide_reference_plus_stage_HUD_bytes=4*720*480,
  parser_wide_banks_plus_one_packet_bytes=4*720*480+49152,
  scope='Declared serial decoder layout projection, not measured Python memory, RTL, RAM placement, routed clock or ESP32 proof. One canonical table reused per color pass; canonical table construction may reread the seekable packet. SHA256 serial workspace budgets 8 chaining+8 working+16 rolling u32 words plus bit count/cursor. CRC/tag passes reread external staged RGB565. Palette fallback overlays table scratch. DMA/FIFO/cache/bus/publication hardware storage is additional and requires implementation. The84480-byte two-bank figure is for measured21120-word HUD. Generic unchanged legacy full-patch syntax permits disjoint total720x480 words, so parser-wide banks require1382400 bytes absent a separately negotiated smaller HUD profile.',
  source_sha256={f:hashlib.sha256((HERE/f).read_bytes()).hexdigest() for f in ('baseline.py','model.py','decoder.py','results.json','resources.py')})
 (HERE/'resources.json').write_text(json.dumps(output,indent=2,sort_keys=True)+'\n')
 print(json.dumps({k:v for k,v in output.items() if k not in ('rows','source_sha256','scope','declared_HS33_logical_layout_bytes')}))
if __name__=='__main__':main()
