// rustc +stable --edition=2021 --test tests/native_attach.rs -o <test.exe>
extern crate self as log;
#[macro_export]
macro_rules! info { ($($arg:tt)*) => { let _ = format!($($arg)*); }; }
mod device {
    pub mod drivers { pub mod fpga {
        pub const REG_FB_DIM: u32 = 0x01000200;
        pub const REG_NATIVE_ABI: u32 = 0x01000204;
        pub const REG_CONTROL: u32 = 0x01000000;
        #[derive(Debug)] pub struct Error;
        impl std::fmt::Display for Error { fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result { write!(f, "mock SPI error") } }
        pub enum Irq { Button }
    }}
    #[derive(Default)]
    pub struct Fpga { pub dim: u32, pub writes: Vec<(u32,u32)>, pub irq: bool, pub fail: bool }
    impl Fpga {
        pub fn read_u32(&mut self, a:u32)->Result<u32,drivers::fpga::Error> {
            if self.fail { Err(drivers::fpga::Error) } else { Ok(match a {
                drivers::fpga::REG_FB_DIM => self.dim,
                drivers::fpga::REG_NATIVE_ABI => 0x5344_4432,
                0x0110_0000 => 0x4742_4d58,
                0x0110_0004 => 0x0001_0000,
                _ => panic!("unexpected FPGA read {a:08x}"),
            }) }
        }
        pub fn write_u32(&mut self,a:u32,v:u32)->Result<(),drivers::fpga::Error> { self.writes.push((a,v)); Ok(()) }
        pub fn enable_interrupt(&mut self,_:drivers::fpga::Irq)->Result<(),drivers::fpga::Error> { self.irq=true; Ok(()) }
    }
    pub struct Device { pub fpga: Fpga }
    impl Device {
        pub fn get()->&'static std::sync::Mutex<Self> {
            static DEVICE: std::sync::OnceLock<std::sync::Mutex<Device>>=std::sync::OnceLock::new();
            DEVICE.get_or_init(||std::sync::Mutex::new(Device{fpga:Fpga::default()}))
        }
        pub fn lock()->std::sync::MutexGuard<'static, Self> {
            Self::get().lock().unwrap()
        }
    }
}
#[path="../src/bitstream/native.rs"] mod native;
#[test]
fn actual_attach_rejects_unknown_and_spi_failure_then_controls_native() {
    for dim in [0, u32::MAX, 160 << 16 | 240] {
        device::Device::lock().fpga = device::Fpga { dim, ..Default::default() };
        assert!(native::attach().is_err());
        let d=device::Device::lock(); assert!(d.fpga.writes.is_empty()); assert!(!d.fpga.irq);
    }
    device::Device::lock().fpga = device::Fpga { dim:800 << 16 | 480, fail:true, ..Default::default() };
    assert!(native::attach().is_err());
    assert!(device::Device::lock().fpga.writes.is_empty());
    device::Device::lock().fpga.fail=false;
    native::attach().unwrap();
    native::control(false,true).unwrap();
    native::control(false,false).unwrap();
    native::control(true,true).unwrap();
    native::control(false,false).unwrap();
    let d=device::Device::lock();
    assert!(d.fpga.irq);
    assert_eq!(d.fpga.writes, [
        (0x0110_0024, 0x4154_5443),
        (0x01000000, 3),
        (0x01000000, 2),
        (0x01000000, 3),
        (0x01000000, 0),
        (0x01000000, 2),
        (0x01000000, 3),
    ]);
}
