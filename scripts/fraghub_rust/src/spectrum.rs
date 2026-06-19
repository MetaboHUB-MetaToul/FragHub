use std::collections::HashMap;

/// Structure de données centrale représentant un spectre de masse.
///
/// Pour un développeur Python : C'est l'équivalent d'une `dataclass` ou d'un dictionnaire typé.
/// L'attribut `#[derive(...)]` demande au compilateur Rust de générer 
/// automatiquement pour nous le code pour copier (`.clone()`), afficher (`print!()` / `Debug`), 
/// et créer un spectre vide (`Spectrum::default()`). C'est extrêmement pratique !
#[derive(Clone, Debug, Default)]
pub struct Spectrum {
    pub metadata: HashMap<String, String>,
    pub peaks: Vec<(f64, f64)>, // Toujours des tuples pour éviter la fragmentation RAM
}
