using System;
internal static class Candidate {
const string Revision=@"USB\VID_1209&PID_B010&REV_0411";
static void Need(bool ok,string message){if(!ok)throw new InvalidOperationException(message);}
static bool Contains(string[] values,string wanted){foreach(string s in values)if(String.Equals(s,wanted,StringComparison.OrdinalIgnoreCase))return true;return false;}
internal static void ValidateTargetSnapshot(string[] hardware,string[] compatible,string[] service,string[] description,uint problem,bool requireUnbound){
        Need(Contains(hardware,Revision),"Exact DFU REV0411 hardware ID required");
        Need(Contains(compatible,@"USB\Class_FF&SubClass_00&Prot_00")&&!Contains(compatible,@"USB\COMPOSITE"),"Exact noncomposite vendor DFU required");
        if(requireUnbound)Need(description.Length==1&&description[0]=="Game Bub Handheld DFU","Exact updater product description required before install");
        else Need(description.Length==1&&description[0]=="WinUsb Device","Expected Microsoft inbox WinUSB description required after install");
        foreach(string s in hardware)Need(s.IndexOf("&MI_",StringComparison.OrdinalIgnoreCase)<0,"Composite child interface is forbidden");
        if(requireUnbound)Need(problem==28&&service.Length==0,"Only unbound code28 updater may be installed");
        else Need(problem==0&&service.Length==1&&String.Equals(service[0],"WINUSB",StringComparison.OrdinalIgnoreCase),"Expected bound WinUSB service/problem0 required after install");
}
}
