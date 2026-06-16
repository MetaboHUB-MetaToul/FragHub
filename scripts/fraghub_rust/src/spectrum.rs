use std::collections::HashMap;

#[derive(Clone, Debug, Default)]
pub struct Spectrum {
    pub metadata: HashMap<String, String>,
    pub peaks: Vec<(f64, f64)>,
}
