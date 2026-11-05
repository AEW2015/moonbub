create_project -in_memory cu70_clock_syntax
create_clock -name shifted -period 10.000 -waveform {7.750 12.750}
puts "CLOCK_SYNTAX_PASS [get_property WAVEFORM [get_clocks shifted]]"
