from pathlib import Path
parent=Path(__file__).with_name('run_tag_bad_tag.py');s=parent.read_text().replace('direct-system/tag-equality-v001','direct-system/tag-phase-cut-v003').replace('6d9e57bd55da26b83ccf8027bb2e4c704329d670b1a73201b0dc40c9ed185433','4159cb208180f94245ed451118aa034e84ba0895f040562aa4df114a8f47f55d');exec(compile(s,str(parent),'exec'),globals())
