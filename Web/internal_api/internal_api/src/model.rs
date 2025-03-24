use serde::Deserialize;

#[derive(Deserialize)]
pub struct Search {
    pub s: String,
}

#[derive(Deserialize)]
pub struct Report {
    pub url: String,
}
