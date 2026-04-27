use pyo3::prelude::*;
use pyo3::types::PyDict;

mod simulation;
use simulation::{ReturnAssumption, SimulationInput, run_simulation};

#[pyfunction]
#[pyo3(signature = (initial_net_worth, cash_flows, allocation, return_assumptions, num_paths, current_age, seed=None))]
fn simulate(
    py: Python<'_>,
    initial_net_worth: f64,
    cash_flows: Vec<f64>,
    allocation: [f64; 4],
    return_assumptions: Vec<(f64, f64)>,
    num_paths: usize,
    current_age: u32,
    seed: Option<u64>,
) -> PyResult<PyObject> {
    if return_assumptions.len() != 4 {
        return Err(pyo3::exceptions::PyValueError::new_err(
            "return_assumptions must have exactly 4 elements"
        ));
    }
    let ra: [ReturnAssumption; 4] = std::array::from_fn(|i| ReturnAssumption {
        mean: return_assumptions[i].0,
        std_dev: return_assumptions[i].1,
    });
    let output = run_simulation(&SimulationInput {
        initial_net_worth, cash_flows,
        allocation, return_assumptions: ra,
        num_paths, current_age, seed,
    });

    let result = PyDict::new_bound(py);
    let by_age_list: Vec<PyObject> = output.by_age.iter().map(|q| {
        let d = PyDict::new_bound(py);
        d.set_item("age", q.age).unwrap();
        d.set_item("p1",  q.p1).unwrap();  d.set_item("p5",  q.p5).unwrap();
        d.set_item("p10", q.p10).unwrap(); d.set_item("p25", q.p25).unwrap();
        d.set_item("p50", q.p50).unwrap(); d.set_item("p75", q.p75).unwrap();
        d.set_item("p90", q.p90).unwrap(); d.set_item("p95", q.p95).unwrap();
        d.set_item("p99", q.p99).unwrap();
        d.into()
    }).collect();
    result.set_item("by_age", by_age_list)?;
    result.set_item("ruin_probability", output.ruin_probability)?;
    Ok(result.into())
}

#[pymodule]
fn rust_core(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(simulate, m)?)?;
    Ok(())
}
