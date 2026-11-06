"""Reuse exact matched base OOC budgets with actual ready/valid feedback closed."""
from pathlib import Path
parent=Path(__file__).with_name('ooc_tag_equality.py');s=parent.read_text()
needle="m=json.loads(manifest.read_text());pins={}"
replacement="m=json.loads(manifest.read_text());wrapper=d/'cu71_tag_feedback_ooc.sv';m['sources'].append(wrapper.relative_to(r).as_posix());m['sources_sha256'][wrapper.relative_to(r).as_posix()]=sha(wrapper);pins={}"
assert needle in s;s=s.replace(needle,replacement)
s=s.replace('synth_design -top cu71_base_pipeline_math ','synth_design -top cu71_tag_feedback_ooc ')
s=s.replace('^canonical/sha/','^base/canonical/sha/')
s=s.replace("'top':'cu71_base_pipeline_math'","'top':'cu71_tag_feedback_ooc'")
s=s.replace("shutil.copyfile(Path(__file__),o/'executed-builder.py');","shutil.copyfile(parent,o/'parent-builder.py');shutil.copyfile(Path(__file__),o/'executed-builder.py');")
exec(compile(s,str(parent),'exec'),globals())
