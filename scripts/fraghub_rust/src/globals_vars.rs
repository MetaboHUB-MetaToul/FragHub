// src/globals_vars.rs

use once_cell::sync::Lazy;
use regex::Regex;

// ==================== Parsers Regex ====================

pub static METADATA_STRIP_VALUE_PATTERN: Lazy<Regex> = Lazy::new(|| Regex::new(r#"^"|"$"#).unwrap());

pub static METADATA_FIELDS_NAME_PATTERN: Lazy<Regex> = Lazy::new(|| Regex::new(r"^[\W_]+|[\W_]+$").unwrap());

pub static METADATA_PATTERN_MGF: Lazy<Regex> = Lazy::new(|| Regex::new(r"([^:\n]*?)=\s*([^\n]*)(?:\n|$)").unwrap());

pub static METADATA_PATTERN_MSP: Lazy<Regex> = Lazy::new(|| Regex::new(r"([^:]*):(?: )?([^\n]*)(?:\n|$)").unwrap());

pub static COMPUTED_PATTERN: Lazy<Regex> = Lazy::new(|| Regex::new(r"(?i)computed").unwrap());

pub static COMMENT_PATTERN: Lazy<Regex> = Lazy::new(|| Regex::new(r"(?i)comment.*").unwrap());

pub static PEAK_LIST_SPLIT_PATTERN: Lazy<Regex> = Lazy::new(|| Regex::new(r"(?:^|\n)(-?\d+\.?\d*(?:[Ee][+-]?\d+)?)(?:\s+|:)(-?\d+[.,]?\d*(?:[Ee][+-]?\d+)?)").unwrap());

pub static PEAK_LIST_JSON_PATTERN: Lazy<Regex> = Lazy::new(|| Regex::new(r"(-?\d+\.?\d*(?:[Ee][+-]?\d+)?)(?:\s+|:|,|, )(-?\d+[.,]?\d*(?:[Ee][+-]?\d+)?)").unwrap());

pub static SUB_FIELDS_PATTERN: Lazy<Regex> = Lazy::new(|| Regex::new(r#"(\S+?)="([^"]*)"|"(\w+?)=([^"]*)"|"([^"]*?)=([^"]*)"|(\S+?)=(\d+(?:[.,]\d*)?)|(\S+?)=(.*?)(?:;|\n|$)"#).unwrap());

// Version corrigée (Greedy, identique à Python) :
// Pour le MSP (On remet [\s\S]* au début et on supprime (?s))
pub static METADATA_PEAK_LIST_SPLIT_PATTERN_MSP: Lazy<Regex> = Lazy::new(|| Regex::new(r"([\s\S]*:.*[0-9]*\n)((?:(?:-?\d+[.,]?\d*(?:[Ee][+-]?\d+)?)(?:\s+|:)(?:-?\d+[.,]?\d*(?:[Ee][+-]?\d+)?).*(?:\n|$))*)").unwrap());

// Pour le MGF (Même chose, on remet [\s\S]* et le =)
pub static METADATA_PEAK_LIST_SPLIT_PATTERN_MGF: Lazy<Regex> = Lazy::new(|| Regex::new(r"([\s\S]*=.*[0-9]*\n)((?:(?:-?\d+[.,]?\d*(?:[Ee][+-]?\d+)?)(?:\s+|:)(?:-?\d+[.,]?\d*(?:[Ee][+-]?\d+)?).*(?:\n|$))*)").unwrap());