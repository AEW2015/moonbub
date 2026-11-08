using System;
using System.IO;
using System.Text;
using System.Collections.Generic;
using System.ComponentModel;
using System.Runtime.InteropServices;
using System.Security.Cryptography;
using System.Security.Principal;
using System.Web.Script.Serialization;
using Microsoft.Win32;

// Default is read-only device/driver enumeration. No self-elevation.
// Only --apply with an exact preflight plan can enter the install branch.
public static class BindGameBubWinUsb {
    const string Target = @"USB\VID_1209&PID_B010\802C0E7A";
    const string Revision = @"USB\VID_1209&PID_B010&REV_0411";
    const string InterfaceGuid = "{EBA74A86-FC4C-46B7-934D-578309693C58}";
    const uint SPDIT_CLASSDRIVER=1, DI_ENUMSINGLEINF=0x10000;
    static readonly IntPtr INVALID = new IntPtr(-1);
    static readonly JavaScriptSerializer Json = new JavaScriptSerializer();

    [StructLayout(LayoutKind.Sequential)] struct DEVINFO { public uint cbSize; public Guid ClassGuid; public uint DevInst; public UIntPtr Reserved; }
    [StructLayout(LayoutKind.Sequential,CharSet=CharSet.Unicode)] struct INSTALLPARAMS {
        public uint cbSize, Flags, FlagsEx; public IntPtr hwndParent, InstallMsgHandler, InstallMsgHandlerContext, FileQueue; public UIntPtr ClassInstallReserved; public uint Reserved;
        [MarshalAs(UnmanagedType.ByValTStr,SizeConst=260)] public string DriverPath;
    }
    [StructLayout(LayoutKind.Sequential,CharSet=CharSet.Unicode)] struct DRIVER {
        public uint cbSize,DriverType; public UIntPtr Reserved;
        [MarshalAs(UnmanagedType.ByValTStr,SizeConst=256)] public string Description;
        [MarshalAs(UnmanagedType.ByValTStr,SizeConst=256)] public string MfgName;
        [MarshalAs(UnmanagedType.ByValTStr,SizeConst=256)] public string ProviderName;
        public uint DateLow,DateHigh; public ulong DriverVersion;
    }
    [StructLayout(LayoutKind.Sequential,CharSet=CharSet.Unicode)] struct DETAIL {
        public uint cbSize,DateLow,DateHigh,CompatIDsOffset,CompatIDsLength; public UIntPtr Reserved;
        [MarshalAs(UnmanagedType.ByValTStr,SizeConst=256)] public string SectionName;
        [MarshalAs(UnmanagedType.ByValTStr,SizeConst=260)] public string InfFileName;
        [MarshalAs(UnmanagedType.ByValTStr,SizeConst=256)] public string Description;
        public ushort FirstHardwareIdChar;
    }
    [DllImport("setupapi.dll",SetLastError=true)] static extern IntPtr SetupDiCreateDeviceInfoList(IntPtr classGuid,IntPtr parent);
    [DllImport("setupapi.dll",CharSet=CharSet.Unicode,SetLastError=true)] static extern bool SetupDiOpenDeviceInfo(IntPtr set,string instance,IntPtr parent,uint flags,ref DEVINFO device);
    [DllImport("setupapi.dll",SetLastError=true)] static extern bool SetupDiDestroyDeviceInfoList(IntPtr set);
    [DllImport("setupapi.dll",CharSet=CharSet.Unicode,SetLastError=true)] static extern bool SetupDiGetDeviceRegistryProperty(IntPtr set,ref DEVINFO device,uint property,out uint type,byte[] buffer,uint size,out uint required);
    [DllImport("setupapi.dll",CharSet=CharSet.Unicode,SetLastError=true)] static extern bool SetupDiGetDeviceInstallParams(IntPtr set,ref DEVINFO device,ref INSTALLPARAMS parameters);
    [DllImport("setupapi.dll",CharSet=CharSet.Unicode,SetLastError=true)] static extern bool SetupDiSetDeviceInstallParams(IntPtr set,ref DEVINFO device,ref INSTALLPARAMS parameters);
    [DllImport("setupapi.dll",SetLastError=true)] static extern bool SetupDiBuildDriverInfoList(IntPtr set,ref DEVINFO device,uint type);
    [DllImport("setupapi.dll",CharSet=CharSet.Unicode,SetLastError=true)] static extern bool SetupDiEnumDriverInfo(IntPtr set,ref DEVINFO device,uint type,uint index,ref DRIVER driver);
    [DllImport("setupapi.dll",CharSet=CharSet.Unicode,SetLastError=true)] static extern bool SetupDiGetDriverInfoDetail(IntPtr set,ref DEVINFO device,ref DRIVER driver,IntPtr detail,uint size,out uint required);
    [DllImport("setupapi.dll",CharSet=CharSet.Unicode,SetLastError=true)] static extern bool SetupDiSetSelectedDriver(IntPtr set,ref DEVINFO device,ref DRIVER driver);
    [DllImport("setupapi.dll",CharSet=CharSet.Unicode,SetLastError=true)] static extern bool SetupDiGetSelectedDriver(IntPtr set,ref DEVINFO device,ref DRIVER driver);
    [DllImport("cfgmgr32.dll")] static extern uint CM_Get_DevNode_Status(out uint status,out uint problem,uint devInst,uint flags);
    [DllImport("newdev.dll",SetLastError=true)] static extern bool DiInstallDevice(IntPtr parent,IntPtr set,ref DEVINFO device,ref DRIVER driver,uint flags,out bool reboot);

    static void Need(bool ok,string message) { if(!ok)throw new InvalidOperationException(message); }
    static void Win(bool ok,string operation) { if(!ok)throw new Win32Exception(Marshal.GetLastWin32Error(),operation); }
    static string Hash(string path) { using(var f=File.OpenRead(path))using(var s=SHA256.Create())return BitConverter.ToString(s.ComputeHash(f)).Replace("-","").ToLowerInvariant(); }
    static string WindowsPath(string suffix) { return Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.Windows),suffix); }
    static string Self { get { return System.Reflection.Assembly.GetExecutingAssembly().Location; } }
    static string[] Property(IntPtr set,ref DEVINFO dev,uint property) {
        byte[] b=new byte[32768];uint type,size;
        if(!SetupDiGetDeviceRegistryProperty(set,ref dev,property,out type,b,(uint)b.Length,out size)) {
            int error=Marshal.GetLastWin32Error(); if(error==13||error==2)return new string[0];throw new Win32Exception(error,"read device property");
        }
        Need(type==1||type==7,"Unexpected string device property type");
        return Encoding.Unicode.GetString(b,0,(int)size).TrimEnd('\0').Split(new char[]{'\0'},StringSplitOptions.RemoveEmptyEntries);
    }
    static bool Contains(string[] values,string wanted) { foreach(string s in values)if(String.Equals(s,wanted,StringComparison.OrdinalIgnoreCase))return true;return false; }
    static object ExistingGuids() {
        using(var key=Registry.LocalMachine.OpenSubKey(@"SYSTEM\CurrentControlSet\Enum\"+Target+@"\Device Parameters")) {
            if(key==null)return null;
            object value=key.GetValue("DeviceInterfaceGUIDs",null,RegistryValueOptions.DoNotExpandEnvironmentNames);
            return value==null ? null : (object)new Dictionary<string,object>{{"kind",key.GetValueKind("DeviceInterfaceGUIDs").ToString()},{"value",value}};
        }
    }
    static Dictionary<string,object> ReadTarget(IntPtr set,ref DEVINFO dev,bool requireUnbound) {
        uint status,problem;Need(CM_Get_DevNode_Status(out status,out problem,dev.DevInst,0)==0,"Target is not a live local devnode");
        string[] hardware=Property(set,ref dev,1),compatible=Property(set,ref dev,2),service=Property(set,ref dev,4),description=Property(set,ref dev,0);
        Need(Contains(hardware,Revision),"Exact DFU REV0411 hardware ID required");
        Need(Contains(compatible,@"USB\Class_FF&SubClass_00&Prot_00")&&!Contains(compatible,@"USB\COMPOSITE"),"Exact noncomposite vendor DFU required");
        Need(description.Length==1&&description[0]=="Game Bub Handheld DFU","Exact updater product description required");
        foreach(string s in hardware)Need(s.IndexOf("&MI_",StringComparison.OrdinalIgnoreCase)<0,"Composite child interface is forbidden");
        if(requireUnbound)Need(problem==28&&service.Length==0,"Only unbound code28 updater may be installed");
        return new Dictionary<string,object>{{"instance",Target},{"expected_revision",Revision},{"problem",problem},{"status",status},{"class_guid",dev.ClassGuid.ToString()},{"hardware_ids",hardware},{"compatible_ids",compatible},{"service",service},{"description",description},{"DeviceInterfaceGUIDs_before",ExistingGuids()}};
    }
    static Dictionary<string,object> DriverMeta(IntPtr set,ref DEVINFO device,ref DRIVER driver) {
        uint required;SetupDiGetDriverInfoDetail(set,ref device,ref driver,IntPtr.Zero,0,out required);
        Need(required>=(uint)Marshal.SizeOf(typeof(DETAIL))&&required<32768,"Unexpected driver detail buffer size");
        IntPtr p=Marshal.AllocHGlobal((int)required);
        try {
            Marshal.WriteInt32(p,Marshal.SizeOf(typeof(DETAIL)));
            Win(SetupDiGetDriverInfoDetail(set,ref device,ref driver,p,required,out required),"target-associated driver details");
            DETAIL detail=(DETAIL)Marshal.PtrToStructure(p,typeof(DETAIL));
            string hardware=Marshal.PtrToStringUni(IntPtr.Add(p,(int)Marshal.OffsetOf(typeof(DETAIL),"FirstHardwareIdChar")));
            return new Dictionary<string,object>{{"description",driver.Description},{"provider",driver.ProviderName},{"manufacturer",driver.MfgName},{"version",driver.DriverVersion.ToString()},{"section",detail.SectionName},{"inf",detail.InfFileName},{"hardware_id",hardware}};
        } finally {Marshal.FreeHGlobal(p);}
    }
    static string ExactInf() {return WindowsPath(@"INF\winusb.inf");}
    static Dictionary<string,object> Enumerate(IntPtr set,ref DEVINFO device,out DRIVER selected) {
        INSTALLPARAMS p=new INSTALLPARAMS();p.cbSize=(uint)Marshal.SizeOf(typeof(INSTALLPARAMS));
        Win(SetupDiGetDeviceInstallParams(set,ref device,ref p),"target install parameters");
        p.Flags|=DI_ENUMSINGLEINF;p.FlagsEx|=0x800;p.DriverPath=ExactInf();
        Win(SetupDiSetDeviceInstallParams(set,ref device,ref p),"target single in-box INF enumeration parameters");
        Win(SetupDiBuildDriverInfoList(set,ref device,SPDIT_CLASSDRIVER),"enumerate target-associated in-box class driver list");
        var rows=new List<object>();selected=new DRIVER();int matches=0;Dictionary<string,object> chosen=null;
        for(uint index=0;index<100;index++) {
            DRIVER d=new DRIVER();d.cbSize=(uint)Marshal.SizeOf(typeof(DRIVER));
            if(!SetupDiEnumDriverInfo(set,ref device,SPDIT_CLASSDRIVER,index,ref d)) {Need(Marshal.GetLastWin32Error()==259,"Unexpected driver enumeration error");break;}
            var row=DriverMeta(set,ref device,ref d);rows.Add(row);
            if(d.ProviderName=="Microsoft"&&(string)row["section"]=="WINUSB"&&String.Equals((string)row["hardware_id"],@"USB\MS_COMP_WINUSB",StringComparison.OrdinalIgnoreCase)&&String.Equals(Path.GetFullPath((string)row["inf"]),ExactInf(),StringComparison.OrdinalIgnoreCase)) {selected=d;chosen=row;matches++;}
        }
        Need(matches==1,"Exactly one Microsoft WINUSB model from the exact in-box INF is required; candidates="+Json.Serialize(rows));
        // Selection is only on this in-memory device-info element; no installation.
        Win(SetupDiSetSelectedDriver(set,ref device,ref selected),"associate selected in-box driver with target element");
        DRIVER fetched=new DRIVER();fetched.cbSize=(uint)Marshal.SizeOf(typeof(DRIVER));
        Win(SetupDiGetSelectedDriver(set,ref device,ref fetched),"get target selected driver");
        var verified=DriverMeta(set,ref device,ref fetched);
        Need(Json.Serialize(verified)==Json.Serialize(chosen),"Target-selected driver differs from exact approved model");
        selected=fetched;
        return new Dictionary<string,object>{{"selected",chosen},{"all_candidates",rows},{"list_scope","target-associated in-memory SPDIT_CLASSDRIVER, DI_ENUMSINGLEINF"},{"set_selected_verified",true},{"get_selected_verified",true},{"target_detail_verified",true},{"device_class_in_memory",device.ClassGuid.ToString()}};
    }
    static void Save(string path,object value) {
        byte[] bytes=Encoding.UTF8.GetBytes(Json.Serialize(value)+Environment.NewLine);
        using(var f=new FileStream(path,FileMode.CreateNew,FileAccess.Write,FileShare.Read)){f.Write(bytes,0,bytes.Length);f.Flush(true);}
    }
    static void WriteGuid() {
        string path=@"SYSTEM\CurrentControlSet\Enum\"+Target+@"\Device Parameters";
        using(var key=Registry.LocalMachine.CreateSubKey(path)) {
            Need(key!=null,"Cannot open exact target Device Parameters");
            var list=new List<string>();object old=key.GetValue("DeviceInterfaceGUIDs");
            if(old!=null){Need(key.GetValueKind("DeviceInterfaceGUIDs")==RegistryValueKind.MultiString,"Existing GUID value type unsupported");list.AddRange((string[])old);}
            if(!list.Exists(delegate(string x){return String.Equals(x,InterfaceGuid,StringComparison.OrdinalIgnoreCase);} ))list.Add(InterfaceGuid);
            key.SetValue("DeviceInterfaceGUIDs",list.ToArray(),RegistryValueKind.MultiString);key.Flush();
        }
    }
    public static int Main(string[] args) {
        IntPtr set=INVALID;string output=null;bool apply=false;string plan=null,instance=null;
        try {
            Need(Environment.Is64BitProcess,"64-bit helper required");
            for(int i=0;i<args.Length;i++) {
                if(args[i]=="--apply")apply=true;
                else if(args[i]=="--output"&&i+1<args.Length)output=args[++i];
                else if(args[i]=="--plan"&&i+1<args.Length)plan=args[++i];
                else if(args[i]=="--expected-instance"&&i+1<args.Length)instance=args[++i];
                else throw new InvalidOperationException("Unknown/incomplete argument");
            }
            Need(output!=null,"--output unique C:/moon directory required");output=Path.GetFullPath(output);
            if(instance!=null)Need(instance==Target,"Only the exact noncomposite updater instance is permitted");
            Need(output.StartsWith(@"C:\moon\",StringComparison.OrdinalIgnoreCase)&&!Directory.Exists(output)&&!File.Exists(output),"Unique output below C:/moon required");
            Directory.CreateDirectory(output);
            set=SetupDiCreateDeviceInfoList(IntPtr.Zero,IntPtr.Zero);Need(set!=INVALID,"Cannot create device info set");
            DEVINFO dev=new DEVINFO();dev.cbSize=(uint)Marshal.SizeOf(typeof(DEVINFO));
            Win(SetupDiOpenDeviceInfo(set,Target,IntPtr.Zero,0,ref dev),"open exact Game Bub updater");
            var before=ReadTarget(set,ref dev,true);DRIVER selected;var drivers=Enumerate(set,ref dev,out selected);
            var hashes=new Dictionary<string,object>{{"helper",Hash(Self)},{"winusb_inf",Hash(ExactInf())},{"winusb_sys",Hash(WindowsPath(@"System32\drivers\WinUSB.sys"))}};
            var preflight=new Dictionary<string,object>{{"schema","moonbub-inbox-winusb-v1"},{"mode",apply?"APPLY_PREFLIGHT":"READ_ONLY_PREFLIGHT"},{"utc",DateTime.UtcNow.ToString("o")},{"before",before},{"drivers",drivers},{"hashes",hashes},{"desired_interface_guid",InterfaceGuid},{"target",Target},{"registry_write_planned",true},{"driver_install_planned",true},{"flash_writes",false},{"sizeof_devinfo",Marshal.SizeOf(typeof(DEVINFO))},{"sizeof_installparams",Marshal.SizeOf(typeof(INSTALLPARAMS))},{"sizeof_driver",Marshal.SizeOf(typeof(DRIVER))},{"sizeof_detail",Marshal.SizeOf(typeof(DETAIL))}};
            Save(Path.Combine(output,"preflight.json"),preflight);
            if(!apply){Save(Path.Combine(output,"result.json"),new{status="READ_ONLY_ENUMERATION_PASS_NO_INSTALL",target=Target});Console.WriteLine("READ_ONLY_ENUMERATION_PASS_NO_INSTALL "+output);return 0;}
            Need(instance==Target,"Explicit exact --expected-instance required");
            Need(plan!=null,"--plan required for apply");
            var previous=Json.Deserialize<Dictionary<string,object>>(File.ReadAllText(plan));
            Need((string)previous["schema"]=="moonbub-inbox-winusb-v1"&&(string)previous["mode"]=="READ_ONLY_PREFLIGHT"&&(string)previous["target"]==Target,"Wrong preflight plan");
            Need(Json.Serialize(previous["hashes"])==Json.Serialize(hashes),"Helper/INF/SYS changed since plan");
            Need(Json.Serialize(previous["before"])==Json.Serialize(before),"Target properties changed since plan");
            Need(Json.Serialize(previous["drivers"])==Json.Serialize(drivers),"Selected in-box driver changed since plan");
            Need(new WindowsPrincipal(WindowsIdentity.GetCurrent()).IsInRole(WindowsBuiltInRole.Administrator),"Administrator token required; no auto-elevation attempted");
            Save(Path.Combine(output,"before-registry-write.json"),new{target=Target,value="DeviceInterfaceGUIDs",data=InterfaceGuid,driver_install_not_yet_called=true});
            WriteGuid();
            Save(Path.Combine(output,"before-driver-install.json"),new{target=Target,driver=drivers["selected"],only_existing_inbox_package=true});
            bool reboot;Win(DiInstallDevice(IntPtr.Zero,set,ref dev,ref selected,0,out reboot),"install selected in-box WinUSB on exact updater");
            var after=ReadTarget(set,ref dev,false);
            Save(Path.Combine(output,"result.json"),new{status="DI_INSTALL_RETURNED_SUCCESS",need_reboot=reboot,target=Target,after=after,flash_writes=false,automatic_reboot=false});
            Console.WriteLine("DI_INSTALL_RETURNED_SUCCESS need_reboot="+reboot);return 0;
        } catch(Exception e) {
            if(output!=null&&Directory.Exists(output))try{Save(Path.Combine(output,"error.json"),new{error=e.GetType().Name,detail=e.Message,apply_requested=apply,flash_writes=false,automatic_retry=false});}catch{}
            Console.Error.WriteLine(e.GetType().Name+": "+e.Message);return 1;
        } finally {if(set!=INVALID)SetupDiDestroyDeviceInfoList(set);}
    }
}
