#!/usr/bin/env python3
"""Arithmetic workload and address bound for a proposed SDRAM JPEG staging path.

This is not an SDRAM command, arbitration, deadline or performance simulator.
"""
from fractions import Fraction
import argparse,json

WORD_BYTES=2
MEMORY_WORDS=1<<20  # current functional model, not a verified fitted part
FB0=0x000000
FB1=0x080000
JPEG0=0x060000
JPEG1=0x0e0000
LCD_WIDTH=480
LCD_HEIGHT=800
SCAN_FETCH_ROWS=720 # LCD code fetches only canvas rows 40..759; margins black
VIDEO_WIDTH=720
VIDEO_HEIGHT=480
BURST_WORDS=8
BURST_BYTES=BURST_WORDS*WORD_BYTES
SDRAM_HZ=100_000_000
# Study's routed MMCM arithmetic: 50 MHz * 56.375 / 3 / 32, divided by
# the source's 541 x 834 raster. No hardware clock measurement implied.
BASELINE_REFRESH=Fraction(50_000_000*451,8*3*32*541*834)

def ceildiv(a,b):
 return (a+b-1)//b

def layout(capacity_bytes):
 if not isinstance(capacity_bytes,int) or capacity_bytes<=0 or capacity_bytes%BURST_BYTES:
  raise ValueError('per-bank capacity must be positive and 16-byte aligned')
 frame_words=LCD_WIDTH*LCD_HEIGHT
 cap_words=capacity_bytes//WORD_BYTES
 regions=[('framebuffer0',FB0,FB0+frame_words),('compressed0',JPEG0,JPEG0+cap_words),
          ('framebuffer1',FB1,FB1+frame_words),('compressed1',JPEG1,JPEG1+cap_words)]
 for name,start,end in regions:
  if start<0 or end>MEMORY_WORDS:raise ValueError(f'{name} exceeds bounded model memory')
 for i,(_,a,b) in enumerate(regions):
  for _,c,d in regions[i+1:]:
   if a<d and c<b:raise ValueError('address regions overlap')
 return [{'name':n,'start_word':a,'end_word_exclusive':b,'bytes':(b-a)*WORD_BYTES} for n,a,b in regions]

def calculate(jpeg_bytes=30000, fps=Fraction(30), refresh=BASELINE_REFRESH,
              capacity_bytes=262144, scan_cycles=Fraction(8), pixel_cycles=Fraction(8),
              jpeg_read_cycles=Fraction(8), jpeg_write_cycles=Fraction(8),
              pixel_burst=True, jpeg_write_burst=True):
 fps,refresh,scan_cycles,pixel_cycles,jpeg_read_cycles,jpeg_write_cycles=map(
  Fraction,(fps,refresh,scan_cycles,pixel_cycles,jpeg_read_cycles,jpeg_write_cycles))
 if fps<=0 or refresh<=0 or any(x<=0 for x in (scan_cycles,pixel_cycles,jpeg_read_cycles,jpeg_write_cycles)):
  raise ValueError('rates and per-request cycle costs must be positive')
 if scan_cycles<BURST_WORDS or jpeg_read_cycles<BURST_WORDS or jpeg_write_cycles<(BURST_WORDS if jpeg_write_burst else 1) or pixel_cycles<(BURST_WORDS if pixel_burst else 1):
  raise ValueError('request cost cannot be shorter than its SDR data beats')
 regions=layout(capacity_bytes)
 if not isinstance(jpeg_bytes,int) or not 0<jpeg_bytes<=capacity_bytes:
  raise ValueError('JPEG byte count must fit a bank')
 padded_jpeg=ceildiv(jpeg_bytes,BURST_BYTES)*BURST_BYTES
 if padded_jpeg>capacity_bytes:raise ValueError('padded JPEG exceeds bank')
 # Scanout fetches 720 canvas rows per refresh, each in 60 BL8 requests;
 # the other 80 physical raster rows display black without SDRAM fetch.
 scan_bursts_per_lcd_frame=SCAN_FETCH_ROWS*ceildiv(LCD_WIDTH,BURST_WORDS)
 # Experimental burst arbiter groups eight transposed pixels. Baseline uses
 # single 16-bit pixel writes; select which request-count hypothesis to assess.
 pixels=VIDEO_WIDTH*VIDEO_HEIGHT
 pixel_requests_per_video_frame=ceildiv(pixels,BURST_WORDS) if pixel_burst else pixels
 jpeg_bursts_per_video_frame=padded_jpeg//BURST_BYTES
 jpeg_write_requests_per_video_frame=(jpeg_bursts_per_video_frame if jpeg_write_burst else padded_jpeg//WORD_BYTES)
 rates={
  'scan_read':Fraction(scan_bursts_per_lcd_frame)*refresh,
  'pixel_write':Fraction(pixel_requests_per_video_frame)*fps,
  'jpeg_write':Fraction(jpeg_write_requests_per_video_frame)*fps,
  'jpeg_read':Fraction(jpeg_bursts_per_video_frame)*fps,
 }
 costs={'scan_read':scan_cycles,'pixel_write':pixel_cycles,
        'jpeg_write':jpeg_write_cycles,'jpeg_read':jpeg_read_cycles}
 request_bytes={'scan_read':BURST_BYTES,'pixel_write':BURST_BYTES if pixel_burst else WORD_BYTES,
                'jpeg_write':BURST_BYTES if jpeg_write_burst else WORD_BYTES,'jpeg_read':BURST_BYTES}
 cycle_rate=sum((rates[k]*costs[k] for k in rates),Fraction())
 data_rate=sum((rates[k]*request_bytes[k] for k in rates),Fraction())
 return {
  'scope':'Arithmetic only; SDRAM cycle costs are hypothetical, not measured; no latency or deadline guarantee.',
  'clock_hz':SDRAM_HZ,'raw_sdr_data_bus_bytes_per_second':SDRAM_HZ*WORD_BYTES,
  'lcd_refresh_hz':float(refresh),'video_fps':float(fps),'jpeg_bytes':jpeg_bytes,
  'padded_jpeg_bytes_each_direction':padded_jpeg,'jpeg_bank_bytes':capacity_bytes,
  'word_address_regions_end_exclusive':regions,
  'scan_bursts_per_lcd_frame':scan_bursts_per_lcd_frame,
  'pixel_write_mode':'BL8_hypothetical_candidate' if pixel_burst else 'single_word_baseline_style',
  'pixel_requests_per_video_frame':pixel_requests_per_video_frame,
  'jpeg_read_bursts_per_video_frame':jpeg_bursts_per_video_frame,
  'jpeg_write_mode':'BL8_hypothetical_candidate' if jpeg_write_burst else 'single_word_baseline_style',
  'jpeg_write_requests_per_video_frame':jpeg_write_requests_per_video_frame,
  'request_rates_per_second':{k:float(v) for k,v in rates.items()},
  'assumed_cycles_per_request':{k:float(v) for k,v in costs.items()},
  'payload_bytes_per_second':{k:float(rates[k]*request_bytes[k]) for k in rates},
  'aggregate_payload_bytes_per_second':float(data_rate),
  'raw_payload_fraction':float(data_rate/(SDRAM_HZ*WORD_BYTES)),
  'hypothetical_required_controller_cycles_per_second':float(cycle_rate),
  'hypothetical_controller_utilization':float(cycle_rate/SDRAM_HZ),
  'hypothetical_cycles_remaining_per_second':float(SDRAM_HZ-cycle_rate),
  'omitted':'Physical timing and SDRAM geometry; row changes, refresh, arbitration, direction changes, contention, deadlines, CDC, QSPI/Wi-Fi and hardware behavior.',
 }

def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--jpeg-bytes',type=int,default=30000)
 p.add_argument('--jpeg-bank-bytes',type=int,default=262144)
 p.add_argument('--fps',type=Fraction,default=Fraction(30))
 p.add_argument('--refresh-hz',type=Fraction,default=BASELINE_REFRESH)
 p.add_argument('--scan-cycles',type=Fraction,default=Fraction(8))
 p.add_argument('--pixel-cycles',type=Fraction,default=Fraction(8))
 p.add_argument('--jpeg-read-cycles',type=Fraction,default=Fraction(8))
 p.add_argument('--jpeg-write-cycles',type=Fraction,default=Fraction(8))
 p.add_argument('--single-pixel-writes',action='store_true')
 p.add_argument('--single-jpeg-writes',action='store_true')
 a=p.parse_args()
 print(json.dumps(calculate(a.jpeg_bytes,a.fps,a.refresh_hz,a.jpeg_bank_bytes,
       a.scan_cycles,a.pixel_cycles,a.jpeg_read_cycles,a.jpeg_write_cycles,
       not a.single_pixel_writes,not a.single_jpeg_writes),indent=2,sort_keys=True))
if __name__=='__main__':main()
