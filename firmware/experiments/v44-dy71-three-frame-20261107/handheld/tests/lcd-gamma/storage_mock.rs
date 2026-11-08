//! Only the NVS transport is mocked; cache and postcard encoding use production code.
pub mod storage {
    pub trait RawStorage {
        fn len(&self, key: &str) -> Result<Option<usize>, std::io::Error>;
        fn get_raw<'a>(
            &self,
            key: &str,
            out: &'a mut [u8],
        ) -> Result<Option<&'a [u8]>, std::io::Error>;
        fn set_raw(&mut self, key: &str, value: &[u8]) -> Result<(), std::io::Error>;
    }
}

pub mod nvs {
    use super::storage::RawStorage;
    use std::{collections::HashMap, marker::PhantomData};
    pub struct NvsCustom;
    pub struct EspNvsPartition<T>(PhantomData<T>);
    impl<T> EspNvsPartition<T> {
        pub fn take(_name: &str) -> Result<Self, std::io::Error> {
            Ok(Self(PhantomData))
        }
    }
    pub struct EspNvs<T> {
        data: HashMap<String, Vec<u8>>,
        kind: PhantomData<T>,
    }
    impl<T> EspNvs<T> {
        pub fn new(_: EspNvsPartition<T>, _: &str, _: bool) -> Result<Self, std::io::Error> {
            Ok(Self {
                data: HashMap::new(),
                kind: PhantomData,
            })
        }
    }
    impl<T> RawStorage for EspNvs<T> {
        fn len(&self, key: &str) -> Result<Option<usize>, std::io::Error> {
            Ok(self.data.get(key).map(Vec::len))
        }
        fn get_raw<'a>(
            &self,
            key: &str,
            out: &'a mut [u8],
        ) -> Result<Option<&'a [u8]>, std::io::Error> {
            Ok(self.data.get(key).map(|value| {
                out[..value.len()].copy_from_slice(value);
                &out[..value.len()]
            }))
        }
        fn set_raw(&mut self, key: &str, value: &[u8]) -> Result<(), std::io::Error> {
            self.data.insert(key.into(), value.to_vec());
            Ok(())
        }
    }
}
