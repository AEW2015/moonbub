//! Generated from immutable original assets-v2 manifest; flashmapped compressed bytes.
pub struct Frame {pub data: &'static [u8], pub crc:u32}
pub struct Loop {pub name:&'static str,pub frames:&'static [Frame]}
static FRAMES_1: [Frame;8] = [
Frame {data:include_bytes!("../../assets/lcd-test-loops/edges_motion/frame_00.jpg"),crc:0xf4c337b2},
Frame {data:include_bytes!("../../assets/lcd-test-loops/edges_motion/frame_01.jpg"),crc:0x8a3133ce},
Frame {data:include_bytes!("../../assets/lcd-test-loops/edges_motion/frame_02.jpg"),crc:0xbc1487ec},
Frame {data:include_bytes!("../../assets/lcd-test-loops/edges_motion/frame_03.jpg"),crc:0xd0c6d127},
Frame {data:include_bytes!("../../assets/lcd-test-loops/edges_motion/frame_04.jpg"),crc:0x1eedb490},
Frame {data:include_bytes!("../../assets/lcd-test-loops/edges_motion/frame_05.jpg"),crc:0x6ed01040},
Frame {data:include_bytes!("../../assets/lcd-test-loops/edges_motion/frame_06.jpg"),crc:0x876be34c},
Frame {data:include_bytes!("../../assets/lcd-test-loops/edges_motion/frame_07.jpg"),crc:0x51e14105},
];
static FRAMES_2: [Frame;8] = [
Frame {data:include_bytes!("../../assets/lcd-test-loops/checker_pan/frame_00.jpg"),crc:0xfaf09071},
Frame {data:include_bytes!("../../assets/lcd-test-loops/checker_pan/frame_01.jpg"),crc:0x8f3a2297},
Frame {data:include_bytes!("../../assets/lcd-test-loops/checker_pan/frame_02.jpg"),crc:0x7889d4b4},
Frame {data:include_bytes!("../../assets/lcd-test-loops/checker_pan/frame_03.jpg"),crc:0x5b2aa434},
Frame {data:include_bytes!("../../assets/lcd-test-loops/checker_pan/frame_04.jpg"),crc:0x0b5479a2},
Frame {data:include_bytes!("../../assets/lcd-test-loops/checker_pan/frame_05.jpg"),crc:0xbf54db19},
Frame {data:include_bytes!("../../assets/lcd-test-loops/checker_pan/frame_06.jpg"),crc:0xe4047fe1},
Frame {data:include_bytes!("../../assets/lcd-test-loops/checker_pan/frame_07.jpg"),crc:0x2bd787b2},
];
static FRAMES_3: [Frame;8] = [
Frame {data:include_bytes!("../../assets/lcd-test-loops/bars_ramp/frame_00.jpg"),crc:0x577ecd0f},
Frame {data:include_bytes!("../../assets/lcd-test-loops/bars_ramp/frame_01.jpg"),crc:0xbd21c6e4},
Frame {data:include_bytes!("../../assets/lcd-test-loops/bars_ramp/frame_02.jpg"),crc:0x840586d0},
Frame {data:include_bytes!("../../assets/lcd-test-loops/bars_ramp/frame_03.jpg"),crc:0xcea792e1},
Frame {data:include_bytes!("../../assets/lcd-test-loops/bars_ramp/frame_04.jpg"),crc:0x2b21f92e},
Frame {data:include_bytes!("../../assets/lcd-test-loops/bars_ramp/frame_05.jpg"),crc:0x71ee19f4},
Frame {data:include_bytes!("../../assets/lcd-test-loops/bars_ramp/frame_06.jpg"),crc:0x789ab1d6},
Frame {data:include_bytes!("../../assets/lcd-test-loops/bars_ramp/frame_07.jpg"),crc:0xf4b0e6ea},
];
pub static LOOPS:[Loop;3] = [
Loop {name:"edges_motion",frames:&FRAMES_1},
Loop {name:"checker_pan",frames:&FRAMES_2},
Loop {name:"bars_ramp",frames:&FRAMES_3},
];
