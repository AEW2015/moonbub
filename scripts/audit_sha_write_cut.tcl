# Read-only matched synthesis check of the ownership-to-storage pipeline cut.
set before [file normalize [lindex $argv 0]]
set after [file normalize [lindex $argv 1]]
set out [file normalize [lindex $argv 2]]
file mkdir $out
set_param general.maxThreads 2
foreach kind {before after} cp [list $before $after] {
 open_checkpoint $cp
 set blocks [get_cells -hier -regexp {^diagnostic/core/key/outer/base_sha/block_reg\[[0-9]+\]$}]
 if {[llength $blocks]!=512} {error "Expected 512 block-storage FFs ($kind)"}
 set targets [get_pins -of_objects $blocks -filter {REF_PIN_NAME == D || REF_PIN_NAME == CE || REF_PIN_NAME == R}]
 set starts [all_fanin -flat -startpoints_only -to $targets]
 set remote {}
 set local {}
 foreach point $starts {
  set cells [get_cells -quiet -of_objects $point]
  foreach cell $cells {
   set name [get_property NAME $cell]
   if {[regexp {^diagnostic/core/key/outer/base_sha/(block_reg\[|block_write_)} $name]} {
    lappend local $name
   } elseif {[get_property REF_NAME $cell] ni {GND VCC}} {
    lappend remote $name
   }
  }
 }
 set remote [lsort -unique $remote]
 set local [lsort -unique $local]
 set f [open [file join $out ${kind}-storage-fanin.txt] w]
 puts $f "checkpoint=$cp"
 puts $f "storage_FFs=[llength $blocks]"
 puts $f "local_sequential_sources=[llength $local]"
 puts $f "remote_sequential_sources=[llength $remote]"
 puts $f "LOCAL=$local"
 puts $f "REMOTE=$remote"
 close $f
 if {$kind eq "before" && [llength $remote]==0} {error "Baseline did not exercise remote input cone"}
 if {$kind eq "after" && ([llength $remote]!=0 || [llength $local]==0)} {error "Pipeline cut not established"}
 close_design
}
puts "SHA_STORAGE_OWNERSHIP_CUT_PASS_MATCHED_SYNTHESIS_ONLY"
