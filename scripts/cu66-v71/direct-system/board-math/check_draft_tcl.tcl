# Parse completeness only. Do not execute Vivado constraints or waive gates.
foreach path $argv {
    set f [open $path r]
    set text [read $f]
    close $f
    if {![info complete $text]} {error "Incomplete Tcl syntax: $path"}
    puts "TCL_COMPLETE_ONLY $path"
}
