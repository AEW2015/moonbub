#!/usr/bin/env python3
"""Read-only source/resource/critical-cone inventory for the unimplemented PCTL1 contract."""
import hashlib,json,re
from fractions import Fraction
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];AREA=Path(__file__).resolve().parent
COUNT=ROOT/'experiments/python-gamebub-v110/count-domain-native/20261108T172431599061Z'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def pin(p):return dict(path=str(p.relative_to(ROOT)),sha256=sha(p),bytes=p.stat().st_size)
def metric(text,label):
 m=re.search(r'^\|\s*'+re.escape(label)+r'\s*\|\s*([0-9.]+)\s*\|',text,re.M);assert m,label
 return float(m[1])if'.'in m[1]else int(m[1])
def main():
 receipt=json.loads((COUNT/'receipt.json').read_text());assert receipt['result']['timing']['WNS_ns']==-1.022 and receipt['clock_period_ns']==10.0
 origins=receipt['source_origins'];sources={}
 for m in origins.values():
  p=ROOT/m['path'];assert sha(p)==m['sha256'];sources[m['path']]=pin(p)
 bind=ROOT/'fpga/build-final/source-bindings.json';bindings=json.loads(bind.read_text());assert len(bindings)==43
 for m in bindings:
  p=ROOT/m['path'];assert p.is_file() and sha(p)==m['sha256'],m['path'];sources[m['path']]=pin(p)
 extra=['docs/cu66-v110/control-contract.md','docs/cu66-v109/integration-gaps.md','docs/cu66-v110/overlap-next.md','docs/external-memory-audit-plan.md','docs/gamebub-v111-v115-simulation-spatial-plan.md','fpga/build-final/clocks.rpt','fpga/experiments/cu66-v111-header/br88_packet_ingress_sync_v91h.sv','experiments/python-gamebub-v111/header/results.json','docs/cu66-v111/header.md']
 for name in extra:p=ROOT/name;sources[name]=pin(p)
 for p in [bind,COUNT/'receipt.json',COUNT/'reports/route-utilization.rpt',COUNT/'reports/route-setup-paths.rpt',ROOT/'fpga/build-final/utilization.rpt']:sources[str(p.relative_to(ROOT))]=pin(p)
 tables={}
 for line in (COUNT/'reports/route-utilization.rpt').read_text().splitlines():
  c=[x.strip()for x in line.split('|')]
  if len(c)==12 and c[3].isdigit():
   tables[c[1]]=dict(module=c[2],total_LUTs=int(c[3]),logic_LUTs=int(c[4]),LUTRAMs=int(c[5]),SRLs=int(c[6]),FFs=int(c[7]),RAMB36=int(c[8]),RAMB18=int(c[9]),DSP=int(c[10]),BRAM36_tiles=int(c[8])+int(c[9])/2)
 custom=tables['cs88_pipeline_v91k'];assert (custom['total_LUTs'],custom['FFs'],custom['RAMB36'],custom['RAMB18'],custom['DSP'])==(36193,35357,32,12,42)
 jpegtext=(ROOT/'fpga/build-final/utilization.rpt').read_text();jpeg=dict(total_LUTs=metric(jpegtext,'Slice LUTs'),FFs=metric(jpegtext,'Slice Registers'),BRAM36_tiles=metric(jpegtext,'Block RAM Tile'),RAMB36=metric(jpegtext,'RAMB36/FIFO*'),RAMB18=metric(jpegtext,'RAMB18'),DSP=metric(jpegtext,'DSPs'),bonded_IOB=metric(jpegtext,'Bonded IOB'))
 assert jpeg==dict(total_LUTs=7362,FFs=5994,BRAM36_tiles=120.5,RAMB36=113,RAMB18=15,DSP=32,bonded_IOB=95)
 paths=[]
 for i,x in enumerate(re.split(r'(?=Slack \()', (COUNT/'reports/route-setup-paths.rpt').read_text())[1:],1):
  sm=re.search(r'Source:\s*([^\n]+)',x);dm=re.search(r'Destination:\s*([^\n]+)',x);assert sm and dm
  source=sm[1].strip();dest=dm[1].strip()
  if 'context_blocks_reg[9]'in source or '/tile_reg[5]'in source:
   t=re.search(r'Data Path Delay:\s*([0-9.]+)ns\s*\(logic ([0-9.]+)ns \(([0-9.]+)%\)\s*route ([0-9.]+)ns \(([0-9.]+)%\)\)',x);assert t
   paths.append(dict(rank=i,source=source,destination=dest,slack_ns=float(re.search(r'Slack.*?:\s*([-0-9.]+)ns',x)[1]),data_delay_ns=float(t[1]),logic_delay_ns=float(t[2]),logic_percent=float(t[3]),route_delay_ns=float(t[4]),route_percent=float(t[5]),logic_levels=re.search(r'Logic Levels:\s*([^\n]+)',x)[1].strip(),reported_cone_resources=[v.strip()for v in re.findall(r'^.*?\s(coefficients/[^\n]+)$',x,re.M)]))
 assert len(paths)==6 and sum('scratch/prepare_block' in x['destination']for x in paths)==4 and sum('/admission/group_visible' in x['destination']for x in paths)==2
 panel=Fraction(50_000_000)*Fraction('56.375')/3/32;refresh=panel/(541*834)
 data=dict(schema='v111-control-contract-source-and-resource-inventory-v1',status='PASS_READ_ONLY_PINNED_INVENTORY_NO_RTL_IMPLEMENTATION',contract_id='PCTL1-V111-SPEC',analysis_script=pin(Path(__file__).resolve()),actual_RTL_run=False,native_implementation=False,hardware_contact=False,clock_125MHz_qualified=False,full_parent_CS88_qualified=False,source_pins=sources,count_actual_source_order=receipt['source_order']if'source_order'in receipt else json.loads((COUNT/'inputs.json').read_text())['source_order'],source_snapshots_match_count_origins=True,historical_JPEG_bindings=dict(path=str(bind.relative_to(ROOT)),sha256=sha(bind),checked=43,matched=43,missing=0,drift=0),resources=dict(device=dict(part='xc7a100tcsg324-1',LUT=63400,FF=126800,BRAM36_tiles=135,DSP=240),historical_JPEG_parent=dict(scope='Retained routed moonshine_top report, Vivado2025.2win64 build6299465, sourcebindings43hashesmatch; not newly implemented',**jpeg),count_component=dict(scope='Actual V110 Count routed OOC cs88_pipeline_v91k, Vivado2026.1 build6511674; no board I/O/parent integration qualification',**custom),count_hierarchy=tables,not_additive=True,shared_resource_reuse_not_implemented=True,arithmetic_remainder_not_allocation=True),remaining_routed_cones=paths,proposed_visibility_ROM=dict(status='UNIMPLEMENTED_DOMAIN_HYPOTHESIS',group_width=16,plane_tiles=[5400,1350,1350],groups=[338,85,85],legal_entries=508,payload_bits=2540,possible_512x5_bits=2560,preconditions=['GROUP_BEGIN group start is multiple16','plane in0..2 and group start below plane tile count','immutable fixed geometry/hidden masks match independent oracle','same-edge successor plane/tile key and owner are correct'],ROM_latency_ports_fit_timing_unverified=True),clock_memory_display=dict(source_input_Hz=50_000_000,source_SPI_overlay_Hz=200_000_000,source_core_memory_Hz=100_000_000,source_SDRAM_read_phase_degrees=279.0,panel_clock_fraction_Hz=[panel.numerator,panel.denominator],panel_clock_nominal_Hz=float(panel),panel_totals=[541,834],panel_refresh_nominal_Hz=float(refresh),panel_active_portrait=[480,800],coded_canvas=[720,480],coded_canvas_portrait_row_offset=40,physical_panel_measurement=False,new_decoder_125MHz_requires_CDC_or_full_system_clock_redesign=True,SDRAM_chip_enable_source='sdram_cke=reset?00:01; sdram_cs_n=10',only_chip0_enabled_in_current_controller=True,full_64MiB_service_or_external_SRAM_path_qualified=False),observability=dict(count_OOC_no_input_delay=receipt['result']['check_timing']['no_input_delay'],count_OOC_no_output_delay=receipt['result']['check_timing']['no_output_delay'],internal_unconstrained=receipt['result']['check_timing']['unconstrained_internal_endpoints'],current_debug_ports_are_public=True,new_snapshot_interface_unimplemented=True),note='This read-only specification/inventory does not alter frozen V111 header qualification or claim any new behavioral, timing, resource-fit or hardware result.')
 (AREA/'inventory.json').write_text(json.dumps(data,indent=2,sort_keys=True)+'\n')
 assert all(sha(ROOT/n)==m['sha256']for n,m in sources.items())
 print(json.dumps(dict(status=data['status'],source_pins=len(sources),remaining_paths=len(paths),JPEG=jpeg,Count=custom,panel_nominal_Hz=float(refresh)),sort_keys=True))
if __name__=='__main__':main()
