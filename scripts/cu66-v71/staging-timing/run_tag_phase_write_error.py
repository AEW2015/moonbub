"""Actual accepted SDRAM write completion error, exact base RTL and real abort."""
from pathlib import Path
parent=Path(__file__).with_name('run_tag_bad_tag.py');s=parent.read_text().replace('direct-system/tag-equality-v001','direct-system/tag-phase-cut-v003').replace('6d9e57bd55da26b83ccf8027bb2e4c704329d670b1a73201b0dc40c9ed185433','4159cb208180f94245ed451118aa034e84ba0895f040562aa4df114a8f47f55d')
s=s.replace("text.count('.expected_tag(canonical_expected)')","text.count('.write_error(write_done_error)')")
s=s.replace("text.replace('.expected_tag(canonical_expected)',\".expected_tag(canonical_expected^128'd1)\")","text.replace('.write_error(write_done_error)',\".write_error(1'b1)\")")
s=s.replace("cpp=(p/'tb.cpp').read_text();start=","cpp=(p/'tb.cpp').read_text().replace('bool transfer=prepared&&result_sent&&candidate;','bool transfer=prepared&&result_sent&&candidate&&!d.error&&!d.aborted;').replace('d.hud_result_valid=prepared&&!result_sent;','d.hud_result_valid=prepared&&!result_sent&&!d.error;');start=")
s=s.replace('0x50','0x61').replace('TAG_EQ_BAD_TAG_ACTUAL_NATIVE_PASS','TAG_PHASE_WRITE_ERROR_NATIVE_PASS')
s=s.replace('PASS_ACTUAL_FULL_KEY_HASH_TAG_MISMATCH_REAL_NATIVE_ABORT_NO_PUBLICATION','PASS_ACTUAL_ACCEPTED_SDRAM_WRITE_ERROR_REAL_NATIVE_ABORT_NO_PUBLICATION')
s=s.replace('Wrong expected_tag at actual base input only; immutable packet/native oracle unchanged','Only write_error at actual base completion input forced1; write_done comes from actual matching accepted SDRAM completion. Client stops new HUD requests on observed error and drains accepted operations.')
exec(compile(s,str(parent),'exec'),globals())
