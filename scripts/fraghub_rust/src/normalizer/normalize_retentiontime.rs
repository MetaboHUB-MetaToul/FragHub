use std::collections::HashMap;

pub fn normalize_retention_time(mut metadata_dict: HashMap<String, String>) -> HashMap<String, String> {
    let rt = metadata_dict.get("RT").cloned().unwrap_or_default();

    if let Some(caps) = crate::globals_vars::RETENTION_TIME_PATTERN.captures(&rt) {
        if let Some(time_match) = caps.get(1) {
            if let Ok(time_val) = time_match.as_str().parse::<f64>() {
                let unit = caps.get(2).map(|m| m.as_str().to_lowercase()).unwrap_or_default();
                let final_rt = match unit.as_str() {
                    "m" | "min" | "minute" | "minutes" | "" => time_val,
                    "s" | "sec" | "second" | "seconds" => time_val / 60.0,
                    "ms" | "millisecond" | "milliseconds" => time_val / 60000.0,
                    _ => time_val, // Par sécurité
                };
                metadata_dict.insert("RT".to_string(), final_rt.to_string());
            }
        }
    }
    metadata_dict
}