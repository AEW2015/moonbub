puts "V100_VERSION [version -short]"
set wanted xc7a100tcsg324-1
set exact [get_parts -quiet $wanted]
puts "V100_TARGET $wanted COUNT [llength $exact]"
set seven [get_parts -quiet xc7*]
puts "V100_SERIES7_COUNT [llength $seven]"
puts "V100_SERIES7_SAMPLE [lrange $seven 0 9]"
set installed [get_parts -quiet]
puts "V100_INSTALLED_COUNT [llength $installed]"
puts "V100_INSTALLED_SAMPLE [lrange $installed 0 9]"
puts "V100_PREFLIGHT_QUERY_COMPLETE"
exit
