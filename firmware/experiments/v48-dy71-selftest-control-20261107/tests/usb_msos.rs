#[path = "../handheld/src/usb_msos.rs"] mod descriptors;
fn le16(b: &[u8], i: usize) -> usize { u16::from_le_bytes([b[i], b[i+1]]) as usize }
fn le32(b: &[u8], i: usize) -> u32 { u32::from_le_bytes(b[i..i+4].try_into().unwrap()) }
fn utf16(b: &[u8]) -> Vec<u16> { assert_eq!(b.len()%2, 0); b.chunks_exact(2).map(|x|u16::from_le_bytes([x[0],x[1]])).collect() }

#[test] fn bos_has_exactly_one_ms_platform_capability() {
    let b = &descriptors::BOS_DESCRIPTOR;
    assert_eq!((b[0],b[1],le16(b,2),b[4]), (5,15,b.len(),1));
    let cap = &b[b[0] as usize..];
    assert_eq!((cap[0] as usize,cap[1],cap[2],cap[3]), (cap.len(),16,5,0));
    assert_eq!(&cap[4..20], &[0xdf,0x60,0xdd,0xd8,0x89,0x45,0xc7,0x4c,0x9c,0xd2,0x65,0x9d,0x9e,0x64,0x8a,0x9f]);
    assert_eq!(le32(cap,20),0x06030000);
    assert_eq!(le16(cap,24), descriptors::OS20_DESCRIPTOR_SET.len());
    assert_eq!((cap[26],cap[27]),(0xf0,0));
    assert!(descriptors::USB_BCD_VERSION>=0x0210);
}

#[test] fn nested_lengths_end_at_the_exact_set_boundary() {
    let b = &descriptors::OS20_DESCRIPTOR_SET;
    assert_eq!((le16(b,0),le16(b,2),le32(b,4)),(10,0,0x06030000));
    assert_eq!(le16(b,8), b.len());
    let config_start=le16(b,0); let function_start=config_start+le16(b,config_start);
    assert_eq!((le16(b,config_start),le16(b,config_start+2),b[config_start+4],b[config_start+5]),(8,1,0,0));
    assert_eq!(config_start+le16(b,config_start+6),b.len());
    assert_eq!((le16(b,function_start),le16(b,function_start+2),b[function_start+4],b[function_start+5]),(8,2,0,0));
    assert_eq!(function_start+le16(b,function_start+6),b.len());
    let mut at=function_start+le16(b,function_start); let mut types=Vec::new();
    while at<b.len(){let n=le16(b,at);assert!(n>=4&&at+n<=b.len());types.push(le16(b,at+2));at+=n;}
    assert_eq!(at,b.len());assert_eq!(types,vec![3,4]);
}

#[test] fn winusb_binds_only_vendor_zero_not_cdc_or_mass_storage() {
    let b=&descriptors::OS20_DESCRIPTOR_SET;
    assert_eq!(descriptors::CONTROL_INTERFACE,0);
    let mut at=0;let mut functions=Vec::new();let mut compatible=Vec::new();
    while at<b.len(){let ty=le16(b,at+2);if ty==2 {functions.push(b[at+4]);}if ty==3 {compatible.push(&b[at+4..at+12]);assert_eq!(&b[at+12..at+20],&[0u8;8]);}at+=le16(b,at);}
    assert_eq!(functions,vec![0]);assert_eq!(compatible,vec![&b"WINUSB\0\0"[..]]);
}

#[test] fn registry_property_is_a_double_terminated_utf16_multi_string() {
    let b=&descriptors::OS20_DESCRIPTOR_SET;let mut at=0;
    while le16(b,at+2)!=4 {at+=le16(b,at);}
    let end=at+le16(b,at);assert_eq!(le16(b,at+4),7);
    let name_len=le16(b,at+6);let name=utf16(&b[at+8..at+8+name_len]);
    assert_eq!(name, "DeviceInterfaceGUIDs\0".encode_utf16().collect::<Vec<_>>());
    let length_at=at+8+name_len;let data_len=le16(b,length_at);let data=&b[length_at+2..end];
    assert_eq!(data_len,data.len());let words=utf16(data);assert_eq!(&words[words.len()-2..],&[0,0]);
    let guid=String::from_utf16(&words[..words.len()-2]).unwrap();
    assert_eq!(guid,descriptors::DEVICE_INTERFACE_GUID);assert_eq!(guid,"{EBA74A86-FC4C-46B7-934D-578309693C58}");
}

#[test] fn ms_request_cannot_intercept_reboot_debug_or_interface_calls() {
    for request in 0..=255u8 {if request!=0xf0{assert!(descriptors::vendor_response(0xc0,request,0,7,178).is_none());}}
    for ty in 0..=255u8 {if ty!=0xc0{assert!(descriptors::vendor_response(ty,0xf0,0,7,178).is_none());}}
    for (value,index,length) in [(1,7,178),(0,0,178),(0,4,178),(0,5,178),(0,7,0)] {
        assert!(descriptors::vendor_response(0xc0,0xf0,value,index,length).is_none());
    }
    assert!(descriptors::vendor_response(0xc1,1,2,0,0).is_none());
}

#[test] fn all_positive_requested_lengths_share_one_immutable_bounded_source() {
    for n in [1,10,177,178,179,u16::MAX] {
        let response=descriptors::vendor_response(0xc0,0xf0,0,7,n).unwrap();
        assert_eq!(response.len(),178);assert_eq!(response.as_ptr(),descriptors::OS20_DESCRIPTOR_SET.as_ptr());
        assert_eq!(response, &descriptors::OS20_DESCRIPTOR_SET);
    }
}

#[test] fn new_lab_revision_is_bcd_and_preserves_supported_mode_ids() {
    for mode in [0,2,3] {
        let revision=descriptors::lab_device_release(mode).unwrap();
        assert_eq!(revision&0xf,mode);assert_eq!(revision&0xfff0,0x4800);
        assert_ne!(revision,0x0400|mode);
        for shift in [0,4,8,12] { assert!(((revision>>shift)&0xf)<=9); }
    }
    for mode in [1,4,8,10,16,0xffff] {assert_eq!(descriptors::lab_device_release(mode),None);}
}
