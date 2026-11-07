open_checkpoint /baseline/synth.dcp
report_utilization -file /work/utilization-flat.rpt
set f [open /work/dsp-registers.tsv w]
puts $f "instance\tprimitive\tAREG\tBREG\tMREG\tPREG"
set dsps [lsort [get_cells -hierarchical -filter {REF_NAME == DSP48E1}]]
foreach cell $dsps {
    puts $f "$cell\t[get_property REF_NAME $cell]\t[get_property AREG $cell]\t[get_property BREG $cell]\t[get_property MREG $cell]\t[get_property PREG $cell]"
}
close $f
puts "V101_ANALYSIS_PART=[get_property PART [current_design]]"
puts "V101_ANALYSIS_DSP_COUNT=[llength $dsps]"
puts "V101_POSTSYNTH_ANALYSIS_COMPLETE"
exit
