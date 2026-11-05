# Readback of this clean run's generated checkpoint; no old/selected inputs.
namespace eval ::Akd1PortableFinalAudit {
 set akd1BuildDir [file normalize [lindex $::argv 0]]
 set akd1AuditDir [file join $akd1BuildDir fresh-drc-audit]
 set_param general.maxThreads 4
 open_checkpoint [file join $akd1BuildDir akd1-clean-routed.dcp]
 report_property [current_design]
 report_route_status -file [file join $akd1AuditDir route-status.rpt]
 report_timing_summary -delay_type min_max -report_unconstrained -file [file join $akd1AuditDir timing-summary.rpt]
 set akd1ActualRule [get_drc_checks REQP-1839]
 puts "PORTABLE_FRESH_RULE CLASS=[get_property CLASS $akd1ActualRule] NAME=[get_property NAME $akd1ActualRule]"
 if {[get_property CLASS $akd1ActualRule] ne "rule_check" || [get_property NAME $akd1ActualRule] ne "REQP-1839"} {error "Actual fresh rule mismatch"}
 report_property $akd1ActualRule
 set_property MAX_MESSAGES 100000 $akd1ActualRule
 # Literal rule name avoids opaque-object header serialization in a long run.
 report_drc -checks REQP-1839 -no_waivers -file [file join $akd1AuditDir drc-reqp1839-full.rpt]
 set akd1Inventory [open [file join $akd1AuditDir reqp1839-inventory.txt] w]
 foreach akd1Entry [get_drc_violations -quiet] {
  if {![string match {REQP-1839#*} [get_property NAME $akd1Entry]] || [get_property IS_WAIVED $akd1Entry]} {error "Unexpected/waived fresh entry"}
  puts $akd1Inventory "$akd1Entry cells=[get_cells -quiet -of_objects $akd1Entry]"
  report_property $akd1Entry
 }
 close $akd1Inventory
 puts "PORTABLE_CLEAN_FRESH_DRC_READBACK_COMPLETE=1"
 close_design
}
