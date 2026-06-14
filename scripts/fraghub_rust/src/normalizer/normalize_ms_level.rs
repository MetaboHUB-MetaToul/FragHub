use std::collections::HashMap;

pub fn normalize_ms_level(mut metadata_dict: HashMap<String, String>) -> HashMap<String, String> {
    let ms_level = metadata_dict.get("MSLEVEL").cloned().unwrap_or_default();

    if !ms_level.is_empty() {
        let matched_levels: Vec<&str> = crate::globals_vars::MS_LEVEL_PATTERN
            .find_iter(&ms_level)
            .map(|m| m.as_str())
            .collect();

        if matched_levels.len() == 1 {
            metadata_dict.insert("MSLEVEL".to_string(), matched_levels[0].to_string());
        } else if matched_levels.len() >= 2 {
            metadata_dict.insert("MSLEVEL".to_string(), format!("{}-{}", matched_levels[0], matched_levels[1]));
        } else {
            metadata_dict.insert("MSLEVEL".to_string(), "2".to_string());
        }
    } else {
        metadata_dict.insert("MSLEVEL".to_string(), "2".to_string());
    }

    metadata_dict
}