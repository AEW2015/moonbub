using System;
internal static class Tests {
 static int checks;
 static bool Accept(bool candidate,string[] h,string[] c,string[] s,string[] d,uint problem,bool before) {
  try {if(candidate)Candidate.ValidateTargetSnapshot(h,c,s,d,problem,before);else Control.ValidateTargetSnapshot(h,c,s,d,problem,before);return true;}
  catch(InvalidOperationException){return false;}
 }
 static void Check(bool ok,string message){checks++;if(!ok)throw new Exception(message);}
 public static int Main(){
  string[][] hardware={new[]{@"USB\VID_1209&PID_B010&REV_0411",@"USB\VID_1209&PID_B010"},new[]{@"USB\VID_1209&PID_B010&REV_0410"},new[]{@"USB\VID_1209&PID_B010&REV_0411",@"USB\VID_1209&PID_B010&MI_00"}};
  string[][] compatible={new[]{@"USB\Class_FF&SubClass_00&Prot_00",@"USB\Class_FF"},new[]{@"USB\Class_FF&SubClass_00&Prot_00",@"USB\COMPOSITE"},new[]{@"USB\Class_FF&SubClass_01&Prot_00"},new string[0]};
  string[][] services={new string[0],new[]{"WINUSB"},new[]{"WUDFRd"},new[]{"WINUSB","OTHER"}};
  string[][] descriptions={new[]{"Game Bub Handheld DFU"},new[]{"WinUsb Device"},new[]{"Unknown Device"},new string[0]};
  uint[] problems={0,28,1};int beforeRows=0,afterRows=0;
  for(int h=0;h<hardware.Length;h++)for(int c=0;c<compatible.Length;c++)for(int s=0;s<services.Length;s++)for(int d=0;d<descriptions.Length;d++)foreach(uint problem in problems) {
   bool expectedBefore=h==0&&c==0&&s==0&&d==0&&problem==28;
   bool expectedAfter=h==0&&c==0&&s==1&&d==1&&problem==0;
   bool original=Accept(false,hardware[h],compatible[c],services[s],descriptions[d],problem,true);
   bool candidate=Accept(true,hardware[h],compatible[c],services[s],descriptions[d],problem,true);
   Check(original==expectedBefore,"control pre-install oracle");Check(candidate==original,"pre-install behavior must be preserved");beforeRows++;
   Check(Accept(true,hardware[h],compatible[c],services[s],descriptions[d],problem,false)==expectedAfter,"strict bound snapshot oracle");afterRows++;
  }
  Check(!Accept(false,hardware[0],compatible[0],services[1],descriptions[1],0,false),"reproduce executed post-description failure");
  Check(Accept(true,hardware[0],compatible[0],services[1],descriptions[1],0,false),"known inbox post snapshot passes corrected predicate");
  Check(!Accept(true,hardware[0],compatible[0],services[1],descriptions[1],0,true),"already-bound node must never pass pre-install");
  Check(!Accept(true,hardware[0],compatible[0],services[0],descriptions[0],28,false),"unbound node must never pass post-install");
  Console.WriteLine("PURE_POSTCHECK_PASS assertions="+checks+" before_matrix="+beforeRows+" after_matrix="+afterRows+" no_SetupAPI_registry_USB_install_calls=true");return 0;
 }
}
