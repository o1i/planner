use pyo3::prelude::*;

mod simulation;

#[pymodule]
fn rust_core(m: &Bound<'_, PyModule>) -> PyResult<()> {
    Ok(())
}
