set target xc7a100tcsg324-1
puts "CU66_VIVADO_VERSION=[version -short]"
set matches [get_parts -quiet $target]
puts "CU66_TARGET=$target"
puts "CU66_TARGET_MATCHES=[llength $matches]"
if {[llength $matches] != 1} {
    puts "CU66_PART_SUPPORT_MISSING"
    exit 2
}
puts "CU66_PART_SUPPORT_PASS"
exit 0
