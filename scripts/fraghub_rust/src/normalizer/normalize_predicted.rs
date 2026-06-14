use std::collections::HashMap;

pub fn normalize_predicted(mut metadata_dict: HashMap<String, String>) -> HashMap<String, String> {
    let predicted = metadata_dict.get("PREDICTED").cloned().unwrap_or_default();
    if predicted.to_lowercase() == "false" {
        return metadata_dict;
    }

    let comment = metadata_dict.get("COMMENT").cloned().unwrap_or_default();
    let filename = metadata_dict.get("FILENAME").cloned().unwrap_or_default();
    let name = metadata_dict.get("NAME").cloned().unwrap_or_default();

    let mut is_predicted = false;
    if crate::globals_vars::IN_SILICO_PATTERN.is_match(&comment) || predicted.to_lowercase() == "true" {
        is_predicted = true;
    } else if !filename.contains("MSMS_Public") {
        let combined = format!("{} {}", filename, name);
        if crate::globals_vars::IN_SILICO_PATTERN.is_match(&combined) {
            is_predicted = true;
        }
    }

    metadata_dict.insert("PREDICTED".to_string(), if is_predicted { "true".to_string() } else { "false".to_string() });
    metadata_dict
}