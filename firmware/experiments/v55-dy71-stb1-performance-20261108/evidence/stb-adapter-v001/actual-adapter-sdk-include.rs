impl Bus for Adapter<'_>{
 fn hbu_status_words(&mut self)->Result<[u32;4],Error>{
  let Some(mut d)=Device::try_lock()else{return Err(Error::Contended)};
  if self.epoch!=Some(d.fpga.program_epoch()){return Err(Error::Epoch)}
  let mut bytes=[0u8;20];self.reads=self.reads.saturating_add(5);self.transactions=self.transactions.saturating_add(1);
  d.fpga.spi_read(Some(MAX_SPI_READ_CLOCK),SpiCommand{word_size:FpgaSpiWordSize::Bits32,byte_swap:false,increment_address:true},0xe0000608,&mut bytes).map_err(|_|Error::Io)?;
  let word=|i:usize|u32::from_be_bytes(bytes[i*4..i*4+4].try_into().unwrap());
  Ok([word(0),word(2),word(3),word(4)])
 }
 // STB1-only ingress. No legacy scalar payload fallback or extra 1KiB bounce.
 fn staging_read_words(&mut self,o:u32,out:&mut[u32])->Result<usize,Error>{
  super::stb1::validate_read(o,out.len()).map_err(|_|Error::Bounds)?;
  let Some(mut d)=Device::try_lock()else{return Err(Error::Contended)};
  let epoch=d.fpga.program_epoch();if let Some(old)=self.epoch{if old!=epoch{return Err(Error::Epoch)}}else{self.epoch=Some(epoch)}
  let mut bytes=[0u8;24];let n=out.len();self.reads=self.reads.saturating_add(n as u32);self.transactions=self.transactions.saturating_add(1);
  d.fpga.spi_read(Some(MAX_SPI_READ_CLOCK),SpiCommand{word_size:FpgaSpiWordSize::Bits32,byte_swap:false,increment_address:true},0xe0000000+o,&mut bytes[..n*4]).map_err(|_|Error::Io)?;
  for(i,value)in out.iter_mut().enumerate(){*value=u32::from_be_bytes(bytes[i*4..i*4+4].try_into().unwrap());}Ok(n)
 }
 fn staging_descriptor(&mut self,words:&[u32;5])->Result<(),Error>{
  super::stb1::validate_descriptor(words).map_err(|_|Error::Bounds)?;
  let Some(mut d)=Device::try_lock()else{return Err(Error::Contended)};
  if self.epoch!=Some(d.fpga.program_epoch()){return Err(Error::Epoch)}
  let mut bytes=[0u8;20];super::stb1::descriptor_be(words,&mut bytes);
  self.guard.side_effects_begin();self.writes=self.writes.saturating_add(5);self.transactions=self.transactions.saturating_add(1);
  d.fpga.spi_write(Some(MAX_SPI_READ_CLOCK),SpiCommand{word_size:FpgaSpiWordSize::Bits32,byte_swap:false,increment_address:true},0xe0000720,&bytes).map_err(|_|Error::Io)
 }
 fn staging_payload_be(&mut self,o:u32,bytes:&[u8])->Result<usize,Error>{
  super::stb1::validate_raw(o,bytes).map_err(|_|Error::Bounds)?;
  let Some(mut d)=Device::try_lock()else{return Err(Error::Contended)};
  if self.epoch!=Some(d.fpga.program_epoch()){return Err(Error::Epoch)}
  self.guard.side_effects_begin();self.writes=self.writes.saturating_add((bytes.len()/4)as u32);self.transactions=self.transactions.saturating_add(1);
  // Bytes already contain per-word BE serialization in the caller's packet buffer.
  d.fpga.spi_write(Some(MAX_SPI_READ_CLOCK),SpiCommand{word_size:FpgaSpiWordSize::Bits32,byte_swap:false,increment_address:true},0xe0000c00,bytes).map_err(|_|Error::Io)?;Ok(bytes.len())
 }

 fn now(&self)->u64{unsafe{esp_idf_svc::sys::esp_timer_get_time().max(0)as u64}}
 fn yield_now(&mut self){std::thread::yield_now();}
 fn read(&mut self,o:u32)->Result<u32,Error>{if o>=0x1000||o&3!=0{return Err(Error::Bounds)}let Some(mut d)=Device::try_lock()else{return Err(Error::Contended)};let epoch=d.fpga.program_epoch();if let Some(old)=self.epoch{if old!=epoch{return Err(Error::Epoch)}}else{self.epoch=Some(epoch)}let r=d.fpga.read_u32(0xe0000000+o).map_err(|_|Error::Io);self.reads=self.reads.saturating_add(1);self.transactions=self.transactions.saturating_add(1);r}
 fn write(&mut self,o:u32,value:u32)->Result<(),Error>{if o>=0x1000||o&3!=0{return Err(Error::Bounds)}let Some(mut d)=Device::try_lock()else{return Err(Error::Contended)};if self.epoch!=Some(d.fpga.program_epoch()){return Err(Error::Epoch)}self.guard.side_effects_begin();self.writes=self.writes.saturating_add(1);self.transactions=self.transactions.saturating_add(1);d.fpga.spi_write(Some(MAX_SPI_READ_CLOCK),SpiCommand{word_size:FpgaSpiWordSize::Bits32,byte_swap:false,increment_address:true},0xe0000000+o,&value.to_be_bytes()).map_err(|_|Error::Io)}
 fn write_words(&mut self,o:u32,words:&[u32])->Result<(),Error>{
  let end=o.checked_add((words.len()as u32).checked_mul(4).ok_or(Error::Bounds)?).ok_or(Error::Bounds)?;
  if words.is_empty()||words.len()>12||o&3!=0||!((o>=0x40&&end<=0x70)||(o==0x20&&words.len()==2)){return Err(Error::Bounds)}
  let Some(mut d)=Device::try_lock()else{return Err(Error::Contended)};
  if self.epoch!=Some(d.fpga.program_epoch()){return Err(Error::Epoch)}
  let mut b=[0u8;48];for(i,v)in words.iter().enumerate(){b[4*i..4*i+4].copy_from_slice(&v.to_be_bytes());}
  self.guard.side_effects_begin();self.writes=self.writes.saturating_add(words.len()as u32);self.transactions=self.transactions.saturating_add(1);
  d.fpga.spi_write(Some(MAX_SPI_READ_CLOCK),SpiCommand{word_size:FpgaSpiWordSize::Bits32,byte_swap:false,increment_address:true},0xe0000000+o,&b[..words.len()*4]).map_err(|_|Error::Io)
 }
 fn mailbox_reply(&mut self)->Result<[u32;3],Error>{
  let Some(mut d)=Device::try_lock()else{return Err(Error::Contended)};
  if self.epoch!=Some(d.fpga.program_epoch()){return Err(Error::Epoch)}
  let mut b=[0u8;12];self.reads=self.reads.saturating_add(3);self.transactions=self.transactions.saturating_add(1);
  d.fpga.spi_read(Some(MAX_SPI_READ_CLOCK),SpiCommand{word_size:FpgaSpiWordSize::Bits32,byte_swap:false,increment_address:true},0xe0000028,&mut b).map_err(|_|Error::Io)?;
  Ok([u32::from_be_bytes(b[..4].try_into().unwrap()),u32::from_be_bytes(b[4..8].try_into().unwrap()),u32::from_be_bytes(b[8..12].try_into().unwrap())])
 }

 fn bulk_payload_write(&mut self,words:&[u32])->Result<(),Error>{
  if words.is_empty()||words.len()>128{return Err(Error::Bounds)}let Some(mut d)=Device::try_lock()else{return Err(Error::Contended)};if self.epoch!=Some(d.fpga.program_epoch()){return Err(Error::Epoch)}
  let mut b=[0u8;512];for(i,v)in words.iter().enumerate(){b[i*4..i*4+4].copy_from_slice(&v.to_be_bytes());}self.guard.side_effects_begin();self.writes=self.writes.saturating_add(words.len()as u32);self.transactions=self.transactions.saturating_add(1);
  d.fpga.spi_write(Some(MAX_SPI_READ_CLOCK),SpiCommand{word_size:FpgaSpiWordSize::Bits32,byte_swap:false,increment_address:true},0xe0000400,&b[..words.len()*4]).map_err(|_|Error::Io)
 }
 fn bulk_payload_read(&mut self,words:&mut[u32])->Result<(),Error>{
  if words.is_empty()||words.len()>128{return Err(Error::Bounds)}let Some(mut d)=Device::try_lock()else{return Err(Error::Contended)};if self.epoch!=Some(d.fpga.program_epoch()){return Err(Error::Epoch)}let mut b=[0u8;512];self.reads=self.reads.saturating_add(words.len()as u32);self.transactions=self.transactions.saturating_add(1);
  d.fpga.spi_read(Some(MAX_SPI_READ_CLOCK),SpiCommand{word_size:FpgaSpiWordSize::Bits32,byte_swap:false,increment_address:true},0xe0000400,&mut b[..words.len()*4]).map_err(|_|Error::Io)?;for(i,v)in words.iter_mut().enumerate(){*v=u32::from_be_bytes(b[i*4..i*4+4].try_into().unwrap());}Ok(())
 }

}
