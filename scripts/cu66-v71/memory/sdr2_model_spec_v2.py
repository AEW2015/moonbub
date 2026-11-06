"""Winbond W9825G6KH A04 CAS3 DQ-launch convention (new model version).

Primary A04 sections10.2/p18 and11.3/p23 show READ sampled at edge3,
D0 launched from edge5 after tAC, and D0 available for capture at edge6.
CAS3 therefore launches DQ at CL-1 subsequent edges, not CL subsequent edges.
MRS0x033 and the programmed CAS3 setting remain unchanged.
"""
def correct_cas3_launch(text):
    assert text.count('latency=3;')==1, 'Expected one frozen model READ latency assignment'
    assert "a!==13'h033" in text, 'The oracle is specifically BL8/CAS3 mode0x033'
    return text.replace('latency=3;', '''// W9825G6KH A04 p23: READ edge3, D0 launch edge5, capture edge6.
    // Programmed CAS remains3; first DQ launch is CL-1 subsequent edges.
    latency=2;''')


def correct_monitor_refresh_anchor(text):
    """MRS starts interval policy but is not an AUTOREFRESH tRFC event."""
    assert text.count('last_ref=-1.0e9,last_mrs=-1.0e9;')==1
    text=text.replace('last_ref=-1.0e9,last_mrs=-1.0e9;', 'last_ref=-1.0e9,last_deadline_anchor=-1.0e9,last_mrs=-1.0e9;')
    text=text.replace('refresh_tracking&&$realtime-last_ref>7812.5','refresh_tracking&&$realtime-last_deadline_anchor>7812.5')
    assert text.count('last_ref=$realtime;')==2
    text=text.replace('last_ref=$realtime;', 'last_ref=$realtime;last_deadline_anchor=$realtime;',1)
    text=text.replace('last_mrs=$realtime;last_ref=$realtime;refresh_tracking=1;', 'last_mrs=$realtime;last_deadline_anchor=$realtime;refresh_tracking=1;')
    return text
