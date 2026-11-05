# Selected v26 ELF frames — static review only

Individual frames cannot establish task headroom. KeyDiag4096 remains provisional.

| Labels | Frame bytes | Symbol |
| --- | ---: | --- |
| USBtask | 128 | `.hidden <std::thread::builder::Builder>::spawn::<handheld::usb_test::start::{closure#0}, ()>` |
| KeyUSB,Dispatch | 128 | `.hidden <std::thread::builder::Builder>::spawn::<<handheld::key_diag_usb::SdkLauncher as handheld::diag_dispatch::Launcher>::spawn_empty::{closure#0}, ()>` |
| KeyUSB,Dispatch | 32 | `core::ptr::drop_in_place::<std::thread::lifecycle::spawn_unchecked<<handheld::key_diag_usb::SdkLauncher as handheld::diag_dispatch::Launcher>::spawn_empty::{closure#0}, ()>::{closure#1}>` |
| Admission | 176 | `<std::sync::mpmc::context::Context>::with::<<std::sync::mpmc::zero::Channel<handheld::core_admission::DiagnosticPermit>>::recv::{closure#1}, core::result::Result<handheld::core_admission::DiagnosticPermit, std::sync::mpsc::RecvTimeoutError>>::{closure#0}` |
| Admission | 48 | `<std::sync::mpmc::context::Context>::with::<<std::sync::mpmc::zero::Channel<handheld::core_admission::DiagnosticPermit>>::recv::{closure#1}, core::result::Result<handheld::core_admission::DiagnosticPermit, std::sync::mpsc::RecvTimeoutError>>::{closure#2}` |
| Admission | 176 | `<std::sync::mpmc::context::Context>::with::<<std::sync::mpmc::zero::Channel<handheld::core_admission::DiagnosticPermit>>::send::{closure#0}, core::result::Result<(), std::sync::mpmc::error::SendTimeoutError<handheld::core_admission::DiagnosticPermit>>>::{closure#0}` |
| Admission | 48 | `<std::sync::mpmc::context::Context>::with::<<std::sync::mpmc::zero::Channel<handheld::core_admission::DiagnosticPermit>>::send::{closure#0}, core::result::Result<(), std::sync::mpmc::error::SendTimeoutError<handheld::core_admission::DiagnosticPermit>>>::{closure#2}` |
| Admission | 128 | `<std::sync::mpmc::context::Context>::with::<<std::sync::mpmc::array::Channel<handheld::core_admission::DiagnosticPermit>>::recv::{closure#1}, ()>::{closure#0}` |
| Admission | 48 | `<std::sync::mpmc::context::Context>::with::<<std::sync::mpmc::array::Channel<handheld::core_admission::DiagnosticPermit>>::recv::{closure#1}, ()>::{closure#2}` |
| Admission | 128 | `<std::sync::mpmc::context::Context>::with::<<std::sync::mpmc::array::Channel<handheld::core_admission::DiagnosticPermit>>::send::{closure#0}, ()>::{closure#0}` |
| Admission | 48 | `<std::sync::mpmc::context::Context>::with::<<std::sync::mpmc::array::Channel<handheld::core_admission::DiagnosticPermit>>::send::{closure#0}, ()>::{closure#2}` |
| USBtask | 48 | `<std::thread::lifecycle::spawn_unchecked<handheld::usb_test::start::{closure#0}, ()>::{closure#1} as core::ops::function::FnOnce<()>>::call_once::{shim:vtable#0}` |
| KeyUSB,Dispatch | 64 | `<std::thread::lifecycle::spawn_unchecked<<handheld::key_diag_usb::SdkLauncher as handheld::diag_dispatch::Launcher>::spawn_empty::{closure#0}, ()>::{closure#1} as core::ops::function::FnOnce<()>>::call_once::{shim:vtable#0}` |
| Admission | 32 | `<std::sync::mpmc::zero::Packet<handheld::core_admission::DiagnosticPermit>>::wait_ready` |
| Admission | 32 | `.hidden <std::sync::mpmc::zero::Channel<handheld::core_admission::DiagnosticPermit>>::disconnect` |
| Admission | 160 | `.hidden <std::sync::mpmc::zero::Channel<handheld::core_admission::DiagnosticPermit>>::recv` |
| Admission | 176 | `.hidden <std::sync::mpmc::zero::Channel<handheld::core_admission::DiagnosticPermit>>::send` |
| Admission | 48 | `.hidden <std::sync::mpmc::array::Channel<handheld::core_admission::DiagnosticPermit>>::with_capacity` |
| Admission | 32 | `.hidden <std::sync::mpmc::array::Channel<handheld::core_admission::DiagnosticPermit>>::disconnect_senders` |
| Admission | 48 | `.hidden <std::sync::mpmc::array::Channel<handheld::core_admission::DiagnosticPermit>>::disconnect_receivers` |
| Admission | 128 | `.hidden <std::sync::mpmc::array::Channel<handheld::core_admission::DiagnosticPermit>>::recv` |
| Admission | 128 | `.hidden <std::sync::mpmc::array::Channel<handheld::core_admission::DiagnosticPermit>>::send` |
| USBtask | 32 | `.hidden std::panicking::catch_unwind::<(), core::panic::unwind_safe::AssertUnwindSafe<std::thread::lifecycle::spawn_unchecked<handheld::usb_test::start::{closure#0}, ()>::{closure#1}::{closure#0}>>` |
| USBtask,KeyUSB,Dispatch | 48 | `.hidden std::sys::backtrace::__rust_begin_short_backtrace::<std::thread::lifecycle::spawn_unchecked<handheld::usb_test::start::{closure#0}, ()>::{closure#1}::{closure#0}::{closure#0}, ()> (.llvm.12782651777686367706)` |
| USBtask | 512 | `.hidden std::sys::backtrace::__rust_begin_short_backtrace::<handheld::usb_test::start::{closure#0}, ()> (.llvm.12782651777686367706)` |
| KeyUSB,Dispatch | 64 | `.hidden std::sys::backtrace::__rust_begin_short_backtrace::<<handheld::key_diag_usb::SdkLauncher as handheld::diag_dispatch::Launcher>::spawn_empty::{closure#0}, ()> (.llvm.12782651777686367706)` |
| Admission | 32 | `<handheld::core_admission::Error as core::fmt::Debug>::fmt` |
| SDKlogger | 96 | `.hidden esp_idf_svc::log::set_target_level::<&str>` |
| KeyCore | 32 | `.hidden <handheld::key_diag_core::DiagnosticCore>::next_operation` |
| KeyCore | 96 | `<handheld::key_diag_core::DiagnosticCore>::read` |
| KeyCore | 48 | `.hidden <handheld::key_diag_core::DiagnosticCore>::complete` |
| Admission | 32 | `.hidden <alloc::boxed::Box<std::sync::mpmc::list::Block<handheld::core_admission::DiagnosticPermit>>>::new_zeroed_in` |
| KeyCore | 32 | `handheld::key_diag_core::put_header` |
| KeyCore | 32 | `handheld::key_diag_core::valid_status` |
| KeyCore | 32 | `.hidden <&handheld::key_diag_core::Reason as core::fmt::Debug>::fmt` |
| Coordinator | 32 | `.hidden <std::sync::poison::mutex::Mutex<handheld::core_coordinator::Coordinator>>::lock` |
| Admission | 32 | `.hidden <handheld::core_admission::CoreAdmission>::release_av` |
| Admission | 32 | `.hidden <handheld::core_admission::CoreAdmission>::reserve_av` |
| Admission | 32 | `.hidden <handheld::core_admission::CoreAdmission>::reserve_video` |
| Admission | 80 | `.hidden <handheld::core_admission::CoreAdmission>::release_program` |
| Admission | 32 | `.hidden <handheld::core_admission::CoreAdmission>::reserve_program` |
| Admission | 32 | `.hidden <handheld::core_admission::CoreAdmission>::reserve_diagnostic` |
| Admission | 32 | `.hidden <handheld::core_admission::CoreAdmission>::reserve_video_program` |
| FpgaProgram | 192 | `.hidden <handheld::device::drivers::fpga::Fpga<esp_idf_hal::gpio::PinDriver<esp_idf_hal::gpio::AnyInputPin, esp_idf_hal::gpio::Input>, esp_idf_hal::gpio::PinDriver<esp_idf_hal::gpio::AnyOutputPin, esp_idf_hal::gpio::Output>, esp_idf_hal::gpio::PinDriver<esp_idf_hal::gpio::AnyIOPin, esp_idf_hal::gpio::Input>, esp_idf_hal::spi::SpiDeviceDriver<&esp_idf_hal::spi::SpiDriver>>>::program` |
| Admission | 32 | `.hidden <alloc::vec::Vec<std::sync::mpmc::array::Slot<handheld::core_admission::DiagnosticPermit>>>::into_boxed_slice` |
| Admission | 48 | `.hidden <alloc::vec::Vec<std::sync::mpmc::array::Slot<handheld::core_admission::DiagnosticPermit>> as alloc::vec::spec_from_iter::SpecFromIter<std::sync::mpmc::array::Slot<handheld::core_admission::DiagnosticPermit>, core::iter::adapters::map::Map<core::ops::range::Range<usize>, <std::sync::mpmc::array::Channel<handheld::core_admission::DiagnosticPermit>>::with_capacity::{closure#0}>>>::from_iter` |
| KeyUSB,Dispatch | 80 | `.hidden handheld::diag_dispatch::launch::<handheld::key_diag_usb::SdkLauncher>` |
| Admission | 416 | `.hidden std::sync::mpmc::sync_channel::<handheld::core_admission::DiagnosticPermit>` |
| Admission | 80 | `.hidden <std::sync::mpmc::Sender<handheld::core_admission::DiagnosticPermit>>::send` |
| Admission | 64 | `.hidden <std::sync::mpmc::Receiver<handheld::core_admission::DiagnosticPermit>>::recv` |
| Admission | 32 | `.hidden <std::sync::mpmc::Sender<handheld::core_admission::DiagnosticPermit> as core::ops::drop::Drop>::drop` |
| Admission | 32 | `.hidden <std::sync::mpmc::Receiver<handheld::core_admission::DiagnosticPermit> as core::ops::drop::Drop>::drop` |
| Admission | 128 | `<std::sync::mpmc::context::Context>::with::<<std::sync::mpmc::list::Channel<handheld::core_admission::DiagnosticPermit>>::recv::{closure#1}, ()>::{closure#0}` |
| Admission | 48 | `<std::sync::mpmc::context::Context>::with::<<std::sync::mpmc::list::Channel<handheld::core_admission::DiagnosticPermit>>::recv::{closure#1}, ()>::{closure#2}` |
| Admission | 32 | `.hidden <std::sync::mpmc::list::Slot<handheld::core_admission::DiagnosticPermit>>::wait_write (.llvm.14186372894266187088)` |
| Admission | 80 | `.hidden <std::sync::mpmc::list::Channel<handheld::core_admission::DiagnosticPermit>>::disconnect_receivers` |
| Admission | 128 | `.hidden <std::sync::mpmc::list::Channel<handheld::core_admission::DiagnosticPermit>>::recv` |
| Admission | 64 | `.hidden <std::sync::mpmc::list::Channel<handheld::core_admission::DiagnosticPermit>>::send` |
| Admission | 32 | `.hidden <std::sync::mpmc::list::Block<handheld::core_admission::DiagnosticPermit>>::wait_next (.llvm.14186372894266187088)` |
| AVrun | 2480 | `.hidden handheld::streaming::audio::run` |
| AVstep | 96 | `handheld::streaming::audio::step` |
| Admission | 48 | `.hidden <std::sync::mpmc::list::Channel<handheld::core_admission::DiagnosticPermit> as core::ops::drop::Drop>::drop` |
| CoreAccess | 208 | `.hidden handheld::core_access::program::<(), handheld::worker::dispatch::{closure#0}>` |
| CoreAccess | 64 | `.hidden <handheld::core_access::MaintenanceGuard>::acquire` |
| CoreAccess | 32 | `.hidden handheld::core_access::av_drained` |
| CoreAccess | 48 | `.hidden handheld::core_access::finish_program` |
| CoreAccess | 80 | `.hidden handheld::core_access::reserve_program` |
| CoreAccess | 48 | `.hidden handheld::core_access::refuse_diagnostic_peer` |
| CoreAccess | 32 | `.hidden handheld::core_access::av_admit` |
| KeyUSB | 480 | `handheld::key_diag_usb::resource_sample` |
| KeyUSB | 80 | `handheld::key_diag_usb::start` |
| KeyUSB | 528 | `handheld::key_diag_usb::report` |
| KeyUSB | 720 | `.hidden handheld::key_diag_usb::worker` |
| KeyUSB | 64 | `.hidden handheld::key_diag_usb::command` |
| USBvideo | 768 | `.hidden handheld::usb_diag::video` |
| USBruntime | 320 | `.hidden handheld::usb_diag::runtime` |
| KeyUSB,Dispatch | 144 | `.hidden <handheld::key_diag_usb::SdkLauncher as handheld::diag_dispatch::Launcher>::spawn_empty` |
| KeyUSB,Dispatch | 32 | `.hidden <handheld::key_diag_usb::SdkLauncher as handheld::diag_dispatch::Launcher>::release_unissued` |
| KeyUSB,Dispatch | 64 | `.hidden <handheld::key_diag_usb::SdkLauncher as handheld::diag_dispatch::Launcher>::reserve` |
| CoreAccess | 32 | `.hidden <handheld::core_access::MaintenanceGuard as core::ops::drop::Drop>::drop` |
| Admission | 32 | `.hidden <handheld::core_admission::Error as core::fmt::Debug>::fmt (.llvm.6167608936890837194)` |
| Dispatch | 32 | `<handheld::diag_dispatch::StartResult as core::fmt::Debug>::fmt` |
| Coordinator | 64 | `.hidden <handheld::core_coordinator::Coordinator>::av_drained` |
| Coordinator | 32 | `.hidden <handheld::core_coordinator::Coordinator>::receiver_active` |
| Coordinator | 80 | `.hidden <handheld::core_coordinator::Coordinator>::program_finished` |
| Coordinator | 64 | `.hidden <handheld::core_coordinator::Coordinator>::receiver_request` |
| Coordinator | 32 | `.hidden <handheld::core_coordinator::Coordinator>::receiver_stopped` |
| Coordinator | 32 | `.hidden <handheld::core_coordinator::Coordinator>::diagnostic_finished` |
| Coordinator | 32 | `.hidden <handheld::core_coordinator::Coordinator>::maintenance_finished` |
| Coordinator | 32 | `.hidden <handheld::core_coordinator::Coordinator>::unissued_diagnostic_finished` |
| Coordinator | 32 | `.hidden <handheld::core_coordinator::Coordinator>::program` |
| Coordinator | 64 | `.hidden <handheld::core_coordinator::Coordinator>::av_admit` |
| KeyPages | 496 | `.hidden handheld::key_diag_pages::page` |
| KeyPages | 288 | `.hidden handheld::key_diag_pages::resource` |
| KeyCore | 32 | `<handheld::key_diag_core::ResultKind as core::fmt::Debug>::fmt` |
| KeyCore | 48 | `<core::option::Option<handheld::key_diag_core::Reason> as core::fmt::Debug>::fmt` |
| KeyCore | 32 | `<handheld::key_diag_core::Stage as core::fmt::Debug>::fmt` |
| SDKlogger | 32 | `core::ptr::drop_in_place::<esp_idf_svc::log::EspLogger>` |
| SDKlogger | 32 | `core::ptr::drop_in_place::<esp_idf_svc::log::EspStdout>` |
| SDKlogger | 48 | `<esp_idf_svc::log::EspLogger>::initialize_default` |
| SDKlogger | 32 | `<esp_idf_svc::log::EspStdout as core::fmt::Write>::write_str` |
| SDKlogger | 128 | `<esp_idf_svc::log::EspLogger as log::Log>::log` |
| SDKlogger | 32 | `<esp_idf_svc::log::EspStdout as core::ops::drop::Drop>::drop` |
| SDKlogger | 48 | `<esp_idf_svc::log::EspStdout as core::fmt::Write>::write_char` |
| SDKlogger | 32 | `<esp_idf_svc::log::EspStdout as core::fmt::Write>::write_fmt` |
| KeyCore | 32 | `<handheld::key_diag_core::DiagnosticCore>::check_time` |
| KeyCore | 32 | `.hidden <handheld::key_diag_core::DiagnosticCore>::request_stop` |
| Admission | 32 | `.hidden <handheld::core_admission::CoreAdmission>::activate_video` |
| Admission | 32 | `.hidden <handheld::core_admission::CoreAdmission>::reserve_restore_program` |
| Coordinator | 32 | `.hidden <handheld::core_coordinator::Coordinator>::maintenance` |
| SDKlogger | 32 | `<esp_idf_svc::log::EspLogger as log::Log>::flush` |
| SDKlogger | 32 | `<esp_idf_svc::log::EspLogger as log::Log>::enabled` |

Not found or inlined: USBcommand

Physical stack/logging/heap/SPI WCET gates: NOT_RUN.
