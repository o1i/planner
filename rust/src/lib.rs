use pyo3::prelude::*;

mod simulation;

#[pymodule]
fn rust_core(_py: Python<'_>, m: &Bound<'_, PyModule>) -> PyResult<()> {
    Ok(())
}
