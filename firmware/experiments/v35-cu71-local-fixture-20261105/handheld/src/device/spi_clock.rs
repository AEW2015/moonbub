//! Pure clock selection and safe conversion of IDF's optional cached result.
pub fn select_rate<I: Iterator<Item = u32>>(rates: I, max_hz: Option<u32>) -> Option<usize> {
    rates.enumerate().find(|(_, rate)| max_hz.map_or(true, |max| *rate <= max)).map(|(i, _)| i)
}
pub fn valid_calculated_khz(rc: i32, khz: i32) -> Option<u32> {
    (rc == 0 && khz > 0).then_some(khz as u32)
}
#[cfg(test)]
mod tests {
    use super::*;
    #[test] fn ordered_device_selection_and_no_match() {
        let rates=[40_000_000,20_000_000,16_000_000,10_000_000];
        assert_eq!(select_rate(rates.into_iter(),Some(40_000_000)),Some(0));
        assert_eq!(select_rate(rates.into_iter(),Some(20_000_000)),Some(1));
        assert_eq!(select_rate(rates.into_iter(),Some(16_000_000)),Some(2));
        assert_eq!(select_rate(rates.into_iter(),None),Some(0));
        assert_eq!(select_rate(rates.into_iter(),Some(1)),None);
    }
    #[test] fn invalid_idf_results_are_unavailable() {
        assert_eq!(valid_calculated_khz(0,40_000),Some(40_000));
        assert_eq!(valid_calculated_khz(1,40_000),None);
        assert_eq!(valid_calculated_khz(0,0),None);
        assert_eq!(valid_calculated_khz(0,-1),None);
    }
}
