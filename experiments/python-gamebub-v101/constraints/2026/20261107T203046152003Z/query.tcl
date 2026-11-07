puts "V101_VERSION=[version -short]"
puts "V101_TARGET_COUNT=[llength [get_parts -quiet xc7a100tcsg324-1]]"
puts "V101_SERIES7_COUNT=[llength [get_parts -quiet xc7*]]"
puts "V101_INSTALLED_PART_COUNT=[llength [get_parts -quiet]]"
puts "V101_QUERY_COMPLETE"
exit
