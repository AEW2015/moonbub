#!/usr/bin/env python3
"""Add observational cycle timestamps to the pinned full-study testbench."""
from pathlib import Path
import sys
s=Path(sys.argv[1]).read_text()
anchor=' task start_frame(input integer id,input integer n);begin'
insert=''' // Observational model-clock timestamps; no control/input is modified.
 longint unsigned m_cycle=0,m_begin=0,m_byte_first=0,m_byte_last=0,m_write_first=0,m_write_last=0,m_drained=0;
 longint unsigned m_reader_start=0,m_read_first=0,m_read_last=0,m_reader_done=0,m_pixel_first=0,m_pixel_last=0,m_present=0;
 integer m_pixel_count=0;
 always @(posedge clk)if(!reset)begin
  m_cycle<=m_cycle+1;
  if(writer_begin&&writer_begin_ready)m_begin<=m_cycle;
  if(stage_enable&&writer_byte_count<n1&&writer_byte_ready)begin
   if(writer_byte_count==0)m_byte_first<=m_cycle;
   if(writer_byte_count==n1-1)m_byte_last<=m_cycle;
  end
  if(stage_wvalid&&stage_wready)begin
   if(stage_write_count==0)m_write_first<=m_cycle;
   if(stage_write_count==stage_total-1)m_write_last<=m_cycle;
  end
  if(writer_done)m_drained<=m_cycle;
  if(sd_start_accept)m_reader_start<=m_cycle;
  if(stage_rvalid&&stage_rready)begin
   if(stage_read_count==0)m_read_first<=m_cycle;
   if(stage_read_count==stage_total-1)m_read_last<=m_cycle;
  end
  if(sd_done)m_reader_done<=m_cycle;
  if(current_id==1&&pix_valid&&!dec_reset&&tile_ready)begin
   if(m_pixel_count==0)m_pixel_first<=m_cycle;
   m_pixel_count<=m_pixel_count+1;
   if(m_pixel_count==345599)m_pixel_last<=m_cycle;
  end
  if(current_id==1&&present)m_present<=m_cycle;
 end
'''
assert s.count(anchor)==1
s=s.replace(anchor,insert+anchor)
anchor='  $display("SDRAM_WRITER_READER_INTEGRATION_PASS bytes=%0d bursts=%0d checked_words=%0d scan_grants=%0d decode_grants=%0d",n1,stage_total,stage_read_words,stage_scan_grants,stage_decode_grants);'
metrics='''  if(!(m_begin>0 && m_begin<=m_byte_first && m_byte_first<=m_byte_last && m_byte_last<=m_write_last && m_write_last<m_drained && m_drained<m_reader_start && m_reader_start<=m_read_first && m_read_first<=m_read_last && m_read_last<=m_reader_done && m_pixel_first>0 && m_pixel_first<=m_pixel_last && m_pixel_last<m_present && m_pixel_count==345600))$fatal(1,"invalid metric event ordering");
  $display("STAGE_TIMING begin=%0d byte_first=%0d byte_last=%0d write_first=%0d write_last=%0d drained=%0d reader_start=%0d read_first=%0d read_last=%0d reader_done=%0d pixel_first=%0d pixel_last=%0d present=%0d",m_begin,m_byte_first,m_byte_last,m_write_first,m_write_last,m_drained,m_reader_start,m_read_first,m_read_last,m_reader_done,m_pixel_first,m_pixel_last,m_present);
'''
assert s.count(anchor)==1
s=s.replace(anchor,metrics+anchor)
Path(sys.argv[2]).write_text(s)
