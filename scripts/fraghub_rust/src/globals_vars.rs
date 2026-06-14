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

pub static EMPTY_PATTERN: Lazy<Regex> = Lazy::new(|| {
    Regex::new(r"(?i)^(?:(?:CCS:( .*)?)|(?:\$:00in-source( .*)?)|(?:0( .*)?)|(?:0\.0( .*)?)|(?:)|(?:na( .*)?)|(?:n/a( .*)?)|(?:nan( .*)?)|(?:unknown( .*)?)|(?:unknow( .*)?)|(?:none( .*)?)|(?:\?( .*)?)|(?:unk( .*)?)|(?:x( .*)?))$").unwrap()
});

// Regex pour les identifiants moléculaires
pub static REPAIR_INCHI_PATTERN: Lazy<Regex> = Lazy::new(|| Regex::new(r"(?i)^(?:inchi=)?").unwrap());

pub static INCHI_PATTERN: Lazy<Regex> = Lazy::new(|| Regex::new(r"(?i)InChI=.*|/[0-9A-Z]*/").unwrap());

pub static SMILES_PATTERN: Lazy<Regex> = Lazy::new(|| Regex::new(r"(?i)[^J][a-z0-9@+\-\[\]\(\)\\/%=#$]{6,}").unwrap());

pub static INCHIKEY_PATTERN: Lazy<Regex> = Lazy::new(|| Regex::new(r"(?i)([A-Z]{14}-[A-Z]{10}-[NO])|([A-Z]{14})").unwrap());

// Regex pour détecter les nombres flottants et les instruments GC
pub static FLOAT_CHECK_PATTERN: Lazy<Regex> = Lazy::new(|| Regex::new(r"(-?\d+[.,]?\d*(?:[Ee][+-]?\d+)?)").unwrap());
pub static GC_PATTERN: Lazy<Regex> = Lazy::new(|| Regex::new(r"(?i)\bGC\b").unwrap());

// Regex pour les modes d'ionisation et les adducts
pub static IONMODE_POS_PATTERN: Lazy<Regex> = Lazy::new(|| Regex::new(r"(?i)^p|^\+|^pos").unwrap());
pub static IONMODE_NEG_PATTERN: Lazy<Regex> = Lazy::new(|| Regex::new(r"(?i)^n|^\-|^neg").unwrap());
pub static SUB_ADDUCT_PATTERN: Lazy<Regex> = Lazy::new(|| Regex::new(r"\(|\)|(.*\[)|(\]([\d\+\-\*]*)?)").unwrap());

// Regex optimisée pour capturer les modes d'ionisation avec détection des limites de mots (\b)
pub static IONIZATION_MODE_PATTERN: Lazy<Regex> = Lazy::new(|| Regex::new(r"(?i)\b(APCI|ACPI|APPI|EI|ESI|FAB|MALDI)\b").unwrap());

// Regex pour les métadonnées (In Silico, MS Level, Retention Time)
pub static IN_SILICO_PATTERN: Lazy<Regex> = Lazy::new(|| Regex::new(r"(?i)in.silico|insilico|predicted|theoretical|Annotation\.level\.3").unwrap());
pub static MS_LEVEL_PATTERN: Lazy<Regex> = Lazy::new(|| Regex::new(r"(?i)(?:ms)?(\d)").unwrap());
pub static RETENTION_TIME_PATTERN: Lazy<Regex> = Lazy::new(|| Regex::new(r"(?i)(-?\d+[.,]?\d*(?:[Ee][+-]?\d+)?)(?:\W)?(m|min|minute|minutes|s|sec|second|seconds|ms|millisecond|milliseconds)(?:\W)?").unwrap());

// Regex pour valider la forme de l'adduct
pub static IS_ADDUCT_PATTERN: Lazy<Regex> = Lazy::new(|| Regex::new(r"(?i)m\]?(\-|\+)").unwrap());

pub static INDIGO_SMILES_CORRECTION_PATTERN: Lazy<Regex> = Lazy::new(|| Regex::new(r"\|[\s\S]*").unwrap());
pub static SUB_SIGNE_END_ADDUCT_PATTERN: Lazy<Regex> = Lazy::new(|| Regex::new(r"(\-|\+)$").unwrap());
