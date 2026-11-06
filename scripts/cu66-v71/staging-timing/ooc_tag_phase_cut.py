"""Clean short-output full-base feedback OOC with structural fanin observation."""
from pathlib import Path
driver=Path(__file__).with_name('ooc_tag_equality.py');s=driver.read_text().replace('direct-system/tag-equality-v001','direct-system/tag-phase-cut-v003').replace("choices=['old','balanced']","choices=['old','phase']")
needle="m=json.loads(manifest.read_text());pins={}"
replacement="m=json.loads(manifest.read_text());wrapper=d/'cu71_tag_feedback_ooc.sv';m['sources'].append(wrapper.relative_to(r).as_posix());m['sources_sha256'][wrapper.relative_to(r).as_posix()]=sha(wrapper);pins={}"
assert needle in s;s=s.replace(needle,replacement).replace('synth_design -top cu71_base_pipeline_math ','synth_design -top cu71_tag_feedback_ooc ').replace('^canonical/sha/','^base/canonical/sha/').replace("'top':'cu71_base_pipeline_math'","'top':'cu71_tag_feedback_ooc'")
observe='''set f [open [file join $out working-CE-fanin.txt] w]
set hash_hits 0
foreach point [lsort -unique [get_property NAME [all_fanin -flat -startpoints_only -to $work_CE]]] {
 puts $f $point
 if {[regexp {^base/canonical/sha/hash_state_reg} $point]} {incr hash_hits}
}
close $f
set write_paths [get_timing_paths -quiet -from [get_ports {write_done write_error}] -to $work_CE -max_paths 1]
set f [open [file join $out phase-cut-structure.txt] w];puts $f "HASH_STATE_FANIN=$hash_hits WRITE_DONE_ERROR_TO_CE_PATHS=[llength $write_paths]";close $f
report_timing -from [get_ports {write_done write_error}] -to $work_CE -max_paths 10 -file [file join $out write-input-to-working-CE.rpt]
'''
s=s.replace('report_timing_summary -delay_type min_max',observe+'\nreport_timing_summary -delay_type min_max')
s=s.replace("shutil.copyfile(Path(__file__),o/'executed-builder.py');","shutil.copyfile(driver,o/'parent-builder.py');shutil.copyfile(Path(__file__),o/'executed-builder.py');")
exec(compile(s,str(driver),'exec'),globals())
