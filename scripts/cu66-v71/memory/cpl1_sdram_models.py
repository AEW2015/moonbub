"""Explicit strict hold-time variant of the frozen functional SDRAM model."""
def strict_hold_text(text):
    assert text.count('T_AC_NS=2.0,')==1
    assert text.count('else if(left>0)begin')==1
    assert text.count('else drive<=#(T_AC_NS) 0;')==1
    text=text.replace('T_AC_NS=2.0,','T_OH_NS=0.5, T_AC_NS=2.0,')
    text=text.replace('else if(left>0)begin',"else if(left>0)begin outdata<=#(T_OH_NS) 16'hxxxx;")
    return text.replace('else drive<=#(T_AC_NS) 0;','else drive<=#(T_OH_NS) 0;')
