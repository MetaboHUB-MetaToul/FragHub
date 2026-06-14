// src/convertors/loaders.rs

use pyo3::prelude::*;
use std::fs::File;
use std::io::{BufRead, BufReader, Read};
use std::path::Path;
use sha2::{Sha256, Digest};
use regex::Regex;
use std::time::{Duration, Instant};

// =========================================================
// LE TUNNEL RUST (JSON) : Protège la RAM contre la copie Python
// =========================================================
#[pyclass]
pub struct RawJsonSpectra {
    pub data: Vec<String>,
}

#[pymethods]
impl RawJsonSpectra {
    fn __len__(&self) -> usize { self.data.len() }
    fn __bool__(&self) -> bool { !self.data.is_empty() }
}

// =========================================================
// LE TUNNEL RUST (MSP) : Protège la RAM contre la copie Python
// =========================================================
#[pyclass]
pub struct RawMspSpectra {
    pub data: Vec<String>,
}

#[pymethods]
impl RawMspSpectra {
    fn __len__(&self) -> usize { self.data.len() }
    fn __bool__(&self) -> bool { !self.data.is_empty() }
}

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

fn count_json_objects(path: &str) -> std::io::Result<usize> {
    let file = File::open(path)?;
    let mut reader = BufReader::with_capacity(1024 * 1024, file);
    let mut count = 0;
    let mut depth = 0;
    let mut in_string = false;
    let mut escaped = false;

    loop {
        let buf = reader.fill_buf()?;
        if buf.is_empty() { break; }
        let length = buf.len();

        for &b in buf {
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
                            if depth == 0 { count += 1; }
                        }
                    }
                    _ => {}
                }
            }
        }
        reader.consume(length);
    }
    Ok(count)
}

// ----------------------------------------------------------------------
// RUST NATIVE JSON LOADER (Array Format - GNPS)
// ----------------------------------------------------------------------
#[pyfunction]
#[pyo3(signature = (json_file_path, progress_callback=None, total_items_callback=None, prefix_callback=None, item_type_callback=None))]
pub fn load_spectrum_list_json(
    py: Python,
    json_file_path: &str,
    progress_callback: Option<PyObject>,
    total_items_callback: Option<PyObject>,
    prefix_callback: Option<PyObject>,
    item_type_callback: Option<PyObject>,
) -> PyResult<RawJsonSpectra> {
    let file_hash = generate_file_hash(json_file_path);
    let path = Path::new(json_file_path);
    let filename = path.file_name().unwrap_or_default().to_string_lossy().to_string();

    let total = count_json_objects(json_file_path).unwrap_or(0);
    if let Some(cb) = &total_items_callback { let _ = cb.call1(py, (total, 0)); }
    if let Some(cb) = &prefix_callback { let _ = cb.call1(py, (format!("loading [{}]:", filename),)); }
    if let Some(cb) = &item_type_callback { let _ = cb.call1(py, ("spectra",)); }

    let file = File::open(json_file_path)?;
    let mut reader = BufReader::with_capacity(1024 * 1024, file);
    let mut spectrum_list = Vec::with_capacity(total);

    let mut depth = 0;
    let mut in_string = false;
    let mut escaped = false;
    let mut buffer = Vec::with_capacity(65536);
    let mut processed = 0;
    let mut last_update = Instant::now();

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
                                let s = String::from_utf8_lossy(&buffer);
                                let injected = s.replacen("{", &format!(r#"{{"filename":"{}","filehash":"{}","#, filename, file_hash), 1);
                                spectrum_list.push(injected);
                                buffer.clear();
                                processed += 1;

                                if last_update.elapsed() >= Duration::from_millis(50) || processed == total {
                                    if let Some(cb) = &progress_callback { let _ = cb.call1(py, (processed,)); }
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
        reader.consume(consumed);
    }
    Ok(RawJsonSpectra { data: spectrum_list })
}

// ----------------------------------------------------------------------
// RUST NATIVE JSONL LOADER (Ligne par Ligne)
// ----------------------------------------------------------------------
#[pyfunction]
#[pyo3(signature = (json_file_path, progress_callback=None, total_items_callback=None, prefix_callback=None, item_type_callback=None))]
pub fn load_spectrum_list_json_2(
    py: Python,
    json_file_path: &str,
    progress_callback: Option<PyObject>,
    total_items_callback: Option<PyObject>,
    prefix_callback: Option<PyObject>,
    item_type_callback: Option<PyObject>,
) -> PyResult<RawJsonSpectra> {
    let file_hash = generate_file_hash(json_file_path);
    let path = Path::new(json_file_path);
    let filename = path.file_name().unwrap_or_default().to_string_lossy().to_string();

    let file = File::open(json_file_path)?;
    let mut reader = BufReader::with_capacity(1024 * 1024, file);
    let mut total = 0;
    let mut buf = [0u8; 65536];

    loop {
        let bytes_read = reader.read(&mut buf)?;
        if bytes_read == 0 { break; }
        for &b in &buf[..bytes_read] {
            if b == b'\n' { total += 1; }
        }
    }

    if let Some(cb) = &total_items_callback { let _ = cb.call1(py, (total, 0)); }
    if let Some(cb) = &prefix_callback { let _ = cb.call1(py, (format!("loading [{}]:", filename),)); }
    if let Some(cb) = &item_type_callback { let _ = cb.call1(py, ("spectra",)); }

    let file2 = File::open(json_file_path)?;
    let mut reader2 = BufReader::with_capacity(1024 * 1024, file2);
    let mut spectrum_list = Vec::with_capacity(total);
    let mut line = String::new();
    let mut processed = 0;
    let mut last_update = Instant::now();

    loop {
        line.clear();
        match reader2.read_line(&mut line) {
            Ok(0) => break,
            Ok(_) => {
                let trimmed = line.trim();
                if !trimmed.is_empty() && trimmed.starts_with('{') {
                    let injected = trimmed.replacen("{", &format!(r#"{{"filename":"{}","filehash":"{}","#, filename, file_hash), 1);
                    spectrum_list.push(injected);

                    processed += 1;
                    if last_update.elapsed() >= Duration::from_millis(50) || processed == total {
                        if let Some(cb) = &progress_callback { let _ = cb.call1(py, (processed,)); }
                        py.allow_threads(|| std::thread::sleep(Duration::from_millis(1)));
                        last_update = Instant::now();
                    }
                }
            }
            Err(e) => return Err(pyo3::exceptions::PyIOError::new_err(e.to_string())),
        }
    }
    Ok(RawJsonSpectra { data: spectrum_list })
}

// ----------------------------------------------------------------------
// MSP FORMAT
// ----------------------------------------------------------------------
#[pyfunction]
#[pyo3(signature = (msp_file_path, progress_callback=None, total_items_callback=None, prefix_callback=None, item_type_callback=None))]
pub fn load_spectrum_list_from_msp(
    py: Python,
    msp_file_path: &str,
    progress_callback: Option<PyObject>,
    total_items_callback: Option<PyObject>,
    prefix_callback: Option<PyObject>,
    item_type_callback: Option<PyObject>,
) -> PyResult<RawMspSpectra> { // RETOURNE L'OBJET NATIF MSP
    let file_hash = generate_file_hash(msp_file_path);
    let path = Path::new(msp_file_path);
    let filename = path.file_name().unwrap_or_default().to_string_lossy().to_string();

    let file = File::open(msp_file_path)?;
    let mut reader = BufReader::new(&file);

    let mut num_spectra = 0;
    let mut line = String::new();
    while reader.read_line(&mut line)? > 0 {
        if line.trim().is_empty() { num_spectra += 1; }
        line.clear();
    }

    if let Some(cb) = &total_items_callback { let _ = cb.call1(py, (num_spectra, 0)); }
    if let Some(cb) = &prefix_callback { let _ = cb.call1(py, (format!("loading [{}]:", filename),)); }
    if let Some(cb) = &item_type_callback { let _ = cb.call1(py, ("spectra",)); }

    let file = File::open(msp_file_path)?;
    let mut reader = BufReader::new(file);
    let mut spectrum_list = Vec::new();
    let mut buffer = vec![format!("FILENAME: {}", filename)];
    let mut processed_spectra = 0;
    let mut last_update = Instant::now();

    let re = Regex::new(r"(?i)FILENAME: .*\n").unwrap();
    let replacement = format!("FILENAME: {}\nFILEHASH: {}\n", filename, file_hash);

    line.clear();
    while reader.read_line(&mut line)? > 0 {
        let trimmed = line.trim();
        if trimmed.is_empty() {
            if buffer.len() > 1 {
                let spectrum = buffer.join("\n") + "\n";
                let replaced = re.replace(&spectrum, replacement.as_str()).to_string();
                spectrum_list.push(replaced.trim_end().to_string());
                buffer = vec![format!("FILENAME: {}", filename)];

                processed_spectra += 1;

                if last_update.elapsed() >= Duration::from_millis(50) || processed_spectra == num_spectra {
                    if let Some(cb) = &progress_callback { let _ = cb.call1(py, (processed_spectra,)); }
                    py.allow_threads(|| std::thread::sleep(Duration::from_millis(1)));
                    last_update = Instant::now();
                }
            }
        } else {
            buffer.push(trimmed.to_string());
        }
        line.clear();
    }

    if buffer.len() > 1 {
        let spectrum = buffer.join("\n") + "\n";
        let replaced = re.replace(&spectrum, replacement.as_str()).to_string();
        spectrum_list.push(replaced.trim_end().to_string());
    }

    Ok(RawMspSpectra { data: spectrum_list })
}

// ----------------------------------------------------------------------
// MGF FORMAT
// ----------------------------------------------------------------------
#[pyfunction]
#[pyo3(signature = (mgf_file_path, progress_callback=None, total_items_callback=None, prefix_callback=None, item_type_callback=None))]
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

    let file = File::open(mgf_file_path)?;
    let mut reader = BufReader::new(&file);

    let mut num_spectra = 0;
    let mut line = String::new();
    while reader.read_line(&mut line)? > 0 {
        if line.trim() == "END IONS" { num_spectra += 1; }
        line.clear();
    }

    if let Some(cb) = &total_items_callback { let _ = cb.call1(py, (num_spectra, 0)); }
    if let Some(cb) = &prefix_callback { let _ = cb.call1(py, (format!("Loading [{}]:", filename),)); }
    if let Some(cb) = &item_type_callback { let _ = cb.call1(py, ("spectra",)); }

    let file = File::open(mgf_file_path)?;
    let mut reader = BufReader::new(file);
    let mut spectrum_list = Vec::new();
    let mut buffer = vec![format!("FILENAME={}", filename)];
    let mut processed_items = 0;
    let mut last_update = Instant::now();

    let re = Regex::new(r"(?i)FILENAME=.*\n").unwrap();
    let replacement = format!("FILENAME={}\nFILEHASH={}\n", filename, file_hash);

    line.clear();
    while reader.read_line(&mut line)? > 0 {
        let trimmed = line.trim();
        if trimmed == "END IONS" {
            if !buffer.is_empty() {
                let spectrum = buffer.join("\n") + "\n";
                let replaced = re.replace(&spectrum, replacement.as_str()).to_string();
                spectrum_list.push(replaced.trim_end().to_string());
                buffer = vec![format!("FILENAME={}", filename)];

                processed_items += 1;

                if last_update.elapsed() >= Duration::from_millis(50) || processed_items == num_spectra {
                    if let Some(cb) = &progress_callback { let _ = cb.call1(py, (processed_items,)); }
                    py.allow_threads(|| std::thread::sleep(Duration::from_millis(1)));
                    last_update = Instant::now();
                }
            }
        } else {
            buffer.push(trimmed.to_string());
        }
        line.clear();
    }

    Ok(spectrum_list)
}