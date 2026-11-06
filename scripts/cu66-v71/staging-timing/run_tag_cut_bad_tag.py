from pathlib import Path
parent=Path(__file__).with_name('run_tag_bad_tag.py');s=parent.read_text();s=s.replace('direct-system/tag-equality-v001','direct-system/tag-feedback-cut-v002').replace('6d9e57bd55da26b83ccf8027bb2e4c704329d670b1a73201b0dc40c9ed185433','b7b0a9165b034d0481bb5a21fd3ff9c3de1822f08a36891f207c1b153177a0a3');exec(compile(s,str(parent),'exec'),globals())
