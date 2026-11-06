# Prospective read-only observation helper. DOES NOT OPEN OR MODIFY A DCP.
# A root-owned future runner must first hash-bind and open the selected parent,
# create a new output directory and set DY_RESET_SNAPSHOT_OUT before sourcing.
if {![info exists DY_RESET_SNAPSHOT_OUT]} {error "Root-selected snapshot output required"}
if {![file isdirectory $DY_RESET_SNAPSHOT_OUT]} {error "Output must be pre-created uniquely"}
set reset_source [get_cells -quiet -hier -regexp {^joint_core_reset_reg\[3\]$}]
if {[llength $reset_source]!=1 || [get_property REF_NAME $reset_source] ne "FDPE"} {error "Unexpected exact DY reset source"}
proc dy_reset_names {objects} {
 if {[llength $objects]==0} {return {}}
 return [lsort -unique [get_property NAME $objects]]
}
proc dy_reset_segments {pin} {return [get_nets -segments -of_objects $pin]}
proc dy_reset_driver_names {pin} {
 return [dy_reset_names [get_pins -leaf -of_objects [dy_reset_segments $pin] -filter {DIRECTION == OUT}]]
}
set q [get_pins -of_objects $reset_source -filter {REF_PIN_NAME == Q}]
if {[llength $q]!=1} {error "Ambiguous source Q"}
set segments [dy_reset_segments $q]
set drivers [dy_reset_driver_names $q]
if {$drivers ne [list joint_core_reset_reg\[3\]/Q]} {error "Unexpected reset net drivers: $drivers"}
if {[llength [get_ports -quiet -of_objects $segments]]!=0} {error "Reset Q has top-level port consumers"}
set leaves [get_pins -leaf -of_objects $segments -filter {DIRECTION == IN}]
set f [open [file join $DY_RESET_SNAPSHOT_OUT reset-leaves.tsv] {WRONLY CREAT EXCL}]
foreach sink [lsort -unique $leaves] {
 set cell [get_cells -of_objects $sink]
 if {[llength $cell]!=1 || ![get_property IS_PRIMITIVE $cell]} {error "Nonprimitive or ambiguous leaf $sink"}
 set net [get_nets -of_objects $sink]
 if {[llength $net]!=1} {error "Ambiguous leaf segment $sink"}
 puts $f [join [list $sink $cell [get_property REF_NAME $cell] [get_property REF_PIN_NAME $sink] [get_property LOC $cell] [get_property BEL $cell] $net [join [dy_reset_driver_names $sink] {|}]] "\t"]
}
close $f
set f [open [file join $DY_RESET_SNAPSHOT_OUT reset-source.tsv] {WRONLY CREAT EXCL}]
foreach prop [lsort [list_property $reset_source]] {
 if {$prop in {REF_NAME INIT ASYNC_REG DONT_TOUCH LOC BEL} || [regexp {^IS_.*_INVERTED$} $prop]} {puts $f [join [list PROPERTY $prop [get_property $prop $reset_source]] "\t"]}
}
foreach name {C CE D PRE} {
 set pin [get_pins -of_objects $reset_source -filter "REF_PIN_NAME == $name"]
 set net [get_nets -of_objects $pin]
 if {[llength $pin]!=1 || [llength $net]!=1} {error "Ambiguous source $name"}
 puts $f [join [list INPUT $name $net [join [dy_reset_driver_names $pin] {|}]] "\t"]
}
close $f
set endpoints [dy_reset_names [all_fanout -flat -endpoints_only -from $q]]
set f [open [file join $DY_RESET_SNAPSHOT_OUT reset-endpoints.txt] {WRONLY CREAT EXCL}]
foreach endpoint $endpoints {puts $f $endpoint};close $f
puts "DY_RESET_READONLY_SNAPSHOT_DIRECT=[llength $leaves] ENDPOINTS=[llength $endpoints] NOT_APPROVED_FOR_ECO"
