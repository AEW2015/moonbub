set_param general.maxThreads 4
set root [file dirname [file normalize [info script]]]
cd $root
create_project -in_memory -part xc7a100tcsg324-1
read_verilog -sv [file join $root {cp23_key_composite_scanout_v008.sv}]
read_verilog -sv [file join $root {cp23_key_private_join.sv}]
read_verilog -sv [file join $root {compute/ar03_envelope.sv}]
read_verilog -sv [file join $root {compute/ar03_inverse.sv}]
read_verilog -sv [file join $root {compute/ar03_key_pipeline_meta.sv}]
read_verilog -sv [file join $root {compute/ar03_key_tagged.sv}]
read_verilog -sv [file join $root {compute/ar03_raster_stripes.sv}]
read_verilog -sv [file join $root {compute/ar03_reconstruct.sv}]
read_verilog -sv [file join $root {compute/canonical_tag.sv}]
read_verilog -sv [file join $root {compute/cp02_decoder.sv}]
read_verilog -sv [file join $root {compute/cp02_key_join.sv}]
read_verilog -sv [file join $root {compute/gm01_sections.sv}]
read_verilog -sv [file join $root {compute/sha256_bytes.sv}]
read_verilog -sv [file join $root {parents/ar03_memory_owned.sv}]
read_verilog -sv [file join $root {parents/ar03_rgb565_kernel.sv}]
read_verilog -sv [file join $root {parents/ar03_yuv_elastic.sv}]
read_verilog -sv [file join $root {parents/ar03_yuv_line_gather.sv}]
read_verilog -sv [file join $root {parents/ar03_yuv_store.sv}]
read_verilog -sv [file join $root {parents/ar03_yuv_store_owned.sv}]
read_verilog -sv [file join $root {parents/ar03_yuv_transpose.sv}]
read_verilog -sv [file join $root {parents/ar03_yuv_transpose_double.sv}]
read_verilog -sv [file join $root {parents/ar03_yuv_transpose_single.sv}]
read_verilog -sv [file join $root {parents/cp23_envelope.sv}]
read_verilog -sv [file join $root {parents/hc22_key_hud.sv}]
read_verilog -sv [file join $root {parents/moonshine_burst_packer.sv}]
read_verilog -sv [file join $root {parents/moonshine_lcd_720p.sv}]
read_verilog -sv [file join $root {parents/moonshine_memory_burst.sv}]
read_verilog -sv [file join $root {parents/moonshine_sdram_burst.sv}]
read_verilog -sv [file join $root {parents/sdram_model_bounded.sv}]
read_xdc [file join $root clocks.xdc]
synth_design -mode out_of_context -top cp23_key_composite_scanout -part xc7a100tcsg324-1
report_utilization -file utilization-new.rpt
report_timing_summary -delay_type min_max -max_paths 10 -report_unconstrained -file timing-new.rpt
report_cdc -details -file cdc-new.rpt
report_drc -file drc-new.rpt
