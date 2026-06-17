// src/convertors/loaders.rs

use pyo3::prelude::*;
use std::fs::File;
use std::io::{BufRead, BufReader};
use std::path::Path;
use sha2::{Sha256, Digest};
use regex::Regex;
use std::time::{Duration, Instant};


/// Gets the size of a file in bytes, converts it to a string, and returns the SHA-256 hash.
#[pyfunction]
pub fn generate_file_hash(file_path: &str) -> String {
    if let Ok(metadata) = std::fs::metadata(file_path) {
        let size = metadata.len().to_string();
        let mut hasher = Sha256::new();
        hasher.update(size.as_bytes());
        format!("{:x}", hasher.finalize())
    } else {
        format!("Error: File not found at {}", file_path)
    }
}

// ----------------------------------------------------------------------
// RUST NATIVE JSON LOADER (Array Format - GNPS)
// ----------------------------------------------------------------------
pub fn load_spectrum_list_json(
    py: Python,
    json_file_path: &str,
    progress_callback: Option<PyObject>,
    total_items_callback: Option<PyObject>,
    prefix_callback: Option<PyObject>,
    item_type_callback: Option<PyObject>,
) -> PyResult<Vec<String>> {
    let file_hash = generate_file_hash(json_file_path);
    let path = Path::new(json_file_path);
    let filename = path.file_name().unwrap_or_default().to_string_lossy().to_string();

    let total_bytes = std::fs::metadata(json_file_path).map(|m| m.len()).unwrap_or(0);
    let total_mb = std::cmp::max(1, total_bytes / (1024 * 1024));

    if let Some(cb) = &total_items_callback { let _ = cb.call1(py, (total_mb, 0)); }
    if let Some(cb) = &prefix_callback { let _ = cb.call1(py, (format!("loading [{}]:", filename),)); }
    if let Some(cb) = &item_type_callback { let _ = cb.call1(py, ("MB",)); }

    let file = File::open(json_file_path)?;
    let mut reader = BufReader::with_capacity(1024 * 1024 * 4, file);
    let mut spectrum_list = Vec::new();

    let mut depth = 0;
    let mut in_string = false;
    let mut escaped = false;
    let mut buffer = Vec::with_capacity(65536);
    let mut total_consumed: u64 = 0;
    let mut last_update = Instant::now();

    let injection_prefix = format!(r#"{{"filename":"{}","filehash":"{}","#, filename, file_hash);

    loop {
        let buf = match reader.fill_buf() {
            Ok(b) => b,
            Err(e) => return Err(pyo3::exceptions::PyIOError::new_err(e.to_string())),
        };
        if buf.is_empty() { break; }

        let mut consumed = 0;

        for &b in buf {
            consumed += 1;
            if depth > 0 || b == b'{' { buffer.push(b); }

            if in_string {
                if escaped { escaped = false; }
                else if b == b'\\' { escaped = true; }
                else if b == b'"' { in_string = false; }
            } else {
                match b {
                    b'"' => in_string = true,
                    b'{' => depth += 1,
                    b'}' => {
                        if depth > 0 {
                            depth -= 1;
                            if depth == 0 {
                                let s = std::str::from_utf8(&buffer).unwrap_or("");
                                if s.starts_with('{') {
                                    let mut injected = String::with_capacity(injection_prefix.len() + s.len());
                                    injected.push_str(&injection_prefix);
                                    injected.push_str(&s[1..]);
                                    spectrum_list.push(injected);
                                }
                                buffer.clear();

                                if last_update.elapsed() >= Duration::from_millis(50) {
                                    let current_mb = (total_consumed + consumed as u64) / (1024 * 1024);
                                    if let Some(cb) = &progress_callback { let _ = cb.call1(py, (current_mb,)); }
                                    py.allow_threads(|| std::thread::sleep(Duration::from_millis(1)));
                                    last_update = Instant::now();
                                }
                            }
                        }
                    }
                    _ => {}
                }
            }
        }
        total_consumed += consumed as u64;
        reader.consume(consumed);
    }
    
    if let Some(cb) = &progress_callback { let _ = cb.call1(py, (total_mb,)); }

    Ok(spectrum_list)
}

// ----------------------------------------------------------------------
// RUST NATIVE JSONL LOADER (Ligne par Ligne)
// ----------------------------------------------------------------------
pub fn load_spectrum_list_json_2(
    py: Python,
    json_file_path: &str,
    progress_callback: Option<PyObject>,
    total_items_callback: Option<PyObject>,
    prefix_callback: Option<PyObject>,
    item_type_callback: Option<PyObject>,
) -> PyResult<Vec<String>> {
    let file_hash = generate_file_hash(json_file_path);
    let path = Path::new(json_file_path);
    let filename = path.file_name().unwrap_or_default().to_string_lossy().to_string();

    let total_bytes = std::fs::metadata(json_file_path).map(|m| m.len()).unwrap_or(0);
    let total_mb = std::cmp::max(1, total_bytes / (1024 * 1024));

    if let Some(cb) = &total_items_callback { let _ = cb.call1(py, (total_mb, 0)); }
    if let Some(cb) = &prefix_callback { let _ = cb.call1(py, (format!("loading [{}]:", filename),)); }
    if let Some(cb) = &item_type_callback { let _ = cb.call1(py, ("MB",)); }

    let file = File::open(json_file_path)?;
    let mut reader = BufReader::with_capacity(1024 * 1024 * 4, file);
    let mut spectrum_list = Vec::new();
    let mut line = String::with_capacity(65536);
    let mut total_consumed: u64 = 0;
    let mut last_update = Instant::now();

    let injection_prefix = format!(r#"{{"filename":"{}","filehash":"{}","#, filename, file_hash);

    loop {
        line.clear();
        match reader.read_line(&mut line) {
            Ok(0) => break,
            Ok(bytes_read) => {
                total_consumed += bytes_read as u64;
                let trimmed = line.trim();
                if !trimmed.is_empty() && trimmed.starts_with('{') {
                    let mut injected = String::with_capacity(injection_prefix.len() + trimmed.len());
                    injected.push_str(&injection_prefix);
                    injected.push_str(&trimmed[1..]);
                    spectrum_list.push(injected);

                    if last_update.elapsed() >= Duration::from_millis(50) {
                        let current_mb = total_consumed / (1024 * 1024);
                        if let Some(cb) = &progress_callback { let _ = cb.call1(py, (current_mb,)); }
                        py.allow_threads(|| std::thread::sleep(Duration::from_millis(1)));
                        last_update = Instant::now();
                    }
                }
            }
            Err(e) => return Err(pyo3::exceptions::PyIOError::new_err(e.to_string())),
        }
    }
    
    if let Some(cb) = &progress_callback { let _ = cb.call1(py, (total_mb,)); }
    
    Ok(spectrum_list)
}

// ----------------------------------------------------------------------
// MSP FORMAT
// ----------------------------------------------------------------------
pub fn load_spectrum_list_from_msp(
    py: Python,
    msp_file_path: &str,
    progress_callback: Option<PyObject>,
    total_items_callback: Option<PyObject>,
    prefix_callback: Option<PyObject>,
    item_type_callback: Option<PyObject>,
) -> PyResult<Vec<String>> { 
    let file_hash = generate_file_hash(msp_file_path);
    let path = Path::new(msp_file_path);
    let filename = path.file_name().unwrap_or_default().to_string_lossy().to_string();

    let total_bytes = std::fs::metadata(msp_file_path).map(|m| m.len()).unwrap_or(0);
    let total_mb = std::cmp::max(1, total_bytes / (1024 * 1024));

    if let Some(cb) = &total_items_callback { let _ = cb.call1(py, (total_mb, 0)); }
    if let Some(cb) = &prefix_callback { let _ = cb.call1(py, (format!("loading [{}]:", filename),)); }
    if let Some(cb) = &item_type_callback { let _ = cb.call1(py, ("MB",)); }

    let file = File::open(msp_file_path)?;
    let mut reader = BufReader::with_capacity(1024 * 1024 * 4, file);
    let mut spectrum_list = Vec::new();
    let mut buffer = vec![format!("FILENAME: {}", filename)];
    let mut total_consumed: u64 = 0;
    let mut last_update = Instant::now();

    let re = Regex::new(r"(?i)FILENAME: .*\n").unwrap();
    let replacement = format!("FILENAME: {}\nFILEHASH: {}\n", filename, file_hash);

    let mut line = String::with_capacity(1024);
    loop {
        line.clear();
        let bytes_read = reader.read_line(&mut line)?;
        if bytes_read == 0 { break; }
        total_consumed += bytes_read as u64;

        let trimmed = line.trim();
        if trimmed.is_empty() {
            if buffer.len() > 1 {
                let spectrum = buffer.join("\n") + "\n";
                let replaced = re.replace(&spectrum, replacement.as_str()).to_string();
                spectrum_list.push(replaced.trim_end().to_string());
                buffer.clear();
                buffer.push(format!("FILENAME: {}", filename));

                if last_update.elapsed() >= Duration::from_millis(50) {
                    let current_mb = total_consumed / (1024 * 1024);
                    if let Some(cb) = &progress_callback { let _ = cb.call1(py, (current_mb,)); }
                    py.allow_threads(|| std::thread::sleep(Duration::from_millis(1)));
                    last_update = Instant::now();
                }
            }
        } else {
            buffer.push(trimmed.to_string());
        }
    }

    if buffer.len() > 1 {
        let spectrum = buffer.join("\n") + "\n";
        let replaced = re.replace(&spectrum, replacement.as_str()).to_string();
        spectrum_list.push(replaced.trim_end().to_string());
    }

    if let Some(cb) = &progress_callback { let _ = cb.call1(py, (total_mb,)); }

    Ok(spectrum_list)
}

// ----------------------------------------------------------------------
// MGF FORMAT
// ----------------------------------------------------------------------
pub fn load_spectrum_list_from_mgf(
    py: Python,
    mgf_file_path: &str,
    progress_callback: Option<PyObject>,
    total_items_callback: Option<PyObject>,
    prefix_callback: Option<PyObject>,
    item_type_callback: Option<PyObject>,
) -> PyResult<Vec<String>> {
    let file_hash = generate_file_hash(mgf_file_path);
    let path = Path::new(mgf_file_path);
    let filename = path.file_name().unwrap_or_default().to_string_lossy().to_string();

    let total_bytes = std::fs::metadata(mgf_file_path).map(|m| m.len()).unwrap_or(0);
    let total_mb = std::cmp::max(1, total_bytes / (1024 * 1024));

    if let Some(cb) = &total_items_callback { let _ = cb.call1(py, (total_mb, 0)); }
    if let Some(cb) = &prefix_callback { let _ = cb.call1(py, (format!("loading [{}]:", filename),)); }
    if let Some(cb) = &item_type_callback { let _ = cb.call1(py, ("MB",)); }

    let file = File::open(mgf_file_path)?;
    let mut reader = BufReader::with_capacity(1024 * 1024 * 4, file);
    let mut spectrum_list = Vec::new();
    let mut buffer = vec![format!("FILENAME={}", filename)];
    let mut total_consumed: u64 = 0;
    let mut last_update = Instant::now();

    let re = Regex::new(r"(?i)FILENAME=.*\n").unwrap();
    let replacement = format!("FILENAME={}\nFILEHASH={}\n", filename, file_hash);

    let mut line = String::with_capacity(1024);
    loop {
        line.clear();
        let bytes_read = reader.read_line(&mut line)?;
        if bytes_read == 0 { break; }
        total_consumed += bytes_read as u64;

        let trimmed = line.trim();
        if trimmed == "END IONS" {
            if !buffer.is_empty() {
                let spectrum = buffer.join("\n") + "\n";
                let replaced = re.replace(&spectrum, replacement.as_str()).to_string();
                spectrum_list.push(replaced.trim_end().to_string());
                buffer.clear();
                buffer.push(format!("FILENAME={}", filename));

                if last_update.elapsed() >= Duration::from_millis(50) {
                    let current_mb = total_consumed / (1024 * 1024);
                    if let Some(cb) = &progress_callback { let _ = cb.call1(py, (current_mb,)); }
                    py.allow_threads(|| std::thread::sleep(Duration::from_millis(1)));
                    last_update = Instant::now();
                }
            }
        } else {
            buffer.push(trimmed.to_string());
        }
    }

    if let Some(cb) = &progress_callback { let _ = cb.call1(py, (total_mb,)); }

    Ok(spectrum_list)
}
