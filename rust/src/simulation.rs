// Monte Carlo simulation engine — pure Rust, no PyO3 dependency

use rand::SeedableRng;
use rand::rngs::StdRng;
use rand_distr::{Normal, Distribution};

pub struct ReturnAssumption {
    /// Annualised log drift (e.g. 0.07 ≈ 7%). For 100% doubling: use ln(2) ≈ 0.693.
    pub mean: f64,
    /// Annualised volatility. Set to 0.0 for deterministic tests.
    pub std_dev: f64,
}

pub struct SimulationInput {
    pub initial_net_worth: f64,
    /// Net CHF added to portfolio per year. Index 0 = first year from now.
    pub cash_flows: Vec<f64>,
    /// [equities, bonds, cash, other] weights summing to 1.0.
    pub allocation: [f64; 4],
    pub return_assumptions: [ReturnAssumption; 4],
    pub num_paths: usize,
    pub current_age: u32,
    pub seed: Option<u64>,
}

pub struct AgeQuantiles {
    pub age: u32,
    pub p1: f64, pub p5: f64, pub p10: f64, pub p25: f64, pub p50: f64,
    pub p75: f64, pub p90: f64, pub p95: f64, pub p99: f64,
}

pub struct SimulationOutput {
    pub by_age: Vec<AgeQuantiles>,
    pub ruin_probability: f64,
}

pub fn run_simulation(input: &SimulationInput) -> SimulationOutput {
    let n_years = input.cash_flows.len();
    let n_paths = input.num_paths;

    // Effective portfolio log-drift and volatility (uncorrelated asset classes).
    let mu_eff: f64 = input.allocation.iter().zip(input.return_assumptions.iter())
        .map(|(w, r)| w * r.mean).sum();
    let var_eff: f64 = input.allocation.iter().zip(input.return_assumptions.iter())
        .map(|(w, r)| w * w * r.std_dev * r.std_dev).sum();
    let sigma_eff = var_eff.sqrt();

    let mut rng: StdRng = match input.seed {
        Some(s) => StdRng::seed_from_u64(s),
        None => StdRng::from_entropy(),
    };

    // net_worths[year][path]
    let mut net_worths: Vec<Vec<f64>> = vec![vec![0.0; n_paths]; n_years + 1];
    for p in 0..n_paths { net_worths[0][p] = input.initial_net_worth; }
    let mut ruin_flags = vec![false; n_paths];

    if sigma_eff < 1e-12 {
        // Deterministic: all paths identical, no random sampling needed.
        let annual_factor = mu_eff.exp();
        for path in 0..n_paths {
            for year in 0..n_years {
                let next = net_worths[year][path] * annual_factor + input.cash_flows[year];
                net_worths[year + 1][path] = next;
                if next <= 0.0 { ruin_flags[path] = true; }
            }
        }
    } else {
        // GBM: annual log return ~ Normal(mu - 0.5σ², σ)
        let log_drift = mu_eff - 0.5 * sigma_eff * sigma_eff;
        let normal = Normal::new(log_drift, sigma_eff).unwrap();
        for path in 0..n_paths {
            for year in 0..n_years {
                let log_r = normal.sample(&mut rng);
                let next = net_worths[year][path] * log_r.exp() + input.cash_flows[year];
                net_worths[year + 1][path] = next;
                if next <= 0.0 { ruin_flags[path] = true; }
            }
        }
    }

    let ruin_count = ruin_flags.iter().filter(|&&f| f).count();

    let quantile = |year: usize, pct: f64| -> f64 {
        let mut vals: Vec<f64> = net_worths[year].clone();
        vals.sort_by(|a, b| a.partial_cmp(b).unwrap());
        let idx = ((pct * (n_paths - 1) as f64).round() as usize).min(n_paths - 1);
        vals[idx]
    };

    let by_age = (0..=n_years).map(|year| AgeQuantiles {
        age: input.current_age + year as u32,
        p1:  quantile(year, 0.01), p5:  quantile(year, 0.05),
        p10: quantile(year, 0.10), p25: quantile(year, 0.25),
        p50: quantile(year, 0.50), p75: quantile(year, 0.75),
        p90: quantile(year, 0.90), p95: quantile(year, 0.95),
        p99: quantile(year, 0.99),
    }).collect();

    SimulationOutput {
        by_age,
        ruin_probability: ruin_count as f64 / n_paths as f64,
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use approx::assert_abs_diff_eq;

    fn equity_only(mean: f64, std_dev: f64) -> ([f64; 4], [ReturnAssumption; 4]) {
        (
            [1.0, 0.0, 0.0, 0.0],
            [
                ReturnAssumption { mean, std_dev },
                ReturnAssumption { mean: 0.0, std_dev: 0.0 },
                ReturnAssumption { mean: 0.0, std_dev: 0.0 },
                ReturnAssumption { mean: 0.0, std_dev: 0.0 },
            ],
        )
    }

    #[test]
    fn zero_return_income_surplus_grows_linearly() {
        // 0% return, +1000 CHF/year net → net worth grows by exactly 1000/year
        let (alloc, ra) = equity_only(0.0, 0.0);
        let out = run_simulation(&SimulationInput {
            initial_net_worth: 0.0,
            cash_flows: vec![1000.0; 10],
            allocation: alloc, return_assumptions: ra,
            num_paths: 5, current_age: 30, seed: Some(42),
        });
        for (i, q) in out.by_age.iter().enumerate() {
            let expected = i as f64 * 1000.0;
            assert_abs_diff_eq!(q.p1,  expected, epsilon = 1e-6);
            assert_abs_diff_eq!(q.p50, expected, epsilon = 1e-6);
            assert_abs_diff_eq!(q.p99, expected, epsilon = 1e-6);
        }
        assert_abs_diff_eq!(out.ruin_probability, 0.0, epsilon = 1e-10);
    }

    #[test]
    fn zero_return_deficit_ruin_at_correct_age() {
        // 0% return, -1000 CHF/year, start 5000 → ruin at year 5 (age 35)
        let (alloc, ra) = equity_only(0.0, 0.0);
        let out = run_simulation(&SimulationInput {
            initial_net_worth: 5000.0,
            cash_flows: vec![-1000.0; 10],
            allocation: alloc, return_assumptions: ra,
            num_paths: 5, current_age: 30, seed: Some(42),
        });
        assert_abs_diff_eq!(out.by_age[5].p50, 0.0,    epsilon = 1e-6);
        assert!(out.by_age[6].p50 < 0.0);
        assert_abs_diff_eq!(out.ruin_probability, 1.0, epsilon = 1e-10);
    }

    #[test]
    fn hundred_percent_return_doubles_each_year() {
        // mu = ln(2), sigma = 0 → net worth doubles each year
        let (alloc, ra) = equity_only(std::f64::consts::LN_2, 0.0);
        let out = run_simulation(&SimulationInput {
            initial_net_worth: 1000.0,
            cash_flows: vec![0.0; 4],
            allocation: alloc, return_assumptions: ra,
            num_paths: 3, current_age: 40, seed: Some(0),
        });
        assert_abs_diff_eq!(out.by_age[0].p50, 1000.0, epsilon = 1e-6);
        assert_abs_diff_eq!(out.by_age[1].p50, 2000.0, epsilon = 1e-6);
        assert_abs_diff_eq!(out.by_age[2].p50, 4000.0, epsilon = 1e-6);
        assert_abs_diff_eq!(out.by_age[3].p50, 8000.0, epsilon = 1e-6);
        assert_abs_diff_eq!(out.ruin_probability, 0.0, epsilon = 1e-10);
    }

    #[test]
    fn one_off_expense_drops_net_worth_at_correct_year() {
        // 0% return, start 10000, one-off -3000 at year index 2 → worth drops at year 3
        let (alloc, ra) = equity_only(0.0, 0.0);
        let mut cash_flows = vec![0.0; 5];
        cash_flows[2] = -3000.0;
        let out = run_simulation(&SimulationInput {
            initial_net_worth: 10000.0,
            cash_flows,
            allocation: alloc, return_assumptions: ra,
            num_paths: 3, current_age: 50, seed: Some(0),
        });
        assert_abs_diff_eq!(out.by_age[2].p50, 10000.0, epsilon = 1e-6);
        assert_abs_diff_eq!(out.by_age[3].p50,  7000.0, epsilon = 1e-6);
        assert_abs_diff_eq!(out.by_age[4].p50,  7000.0, epsilon = 1e-6);
    }

    #[test]
    fn age_offset_applied_correctly() {
        let (alloc, ra) = equity_only(0.0, 0.0);
        let out = run_simulation(&SimulationInput {
            initial_net_worth: 0.0,
            cash_flows: vec![0.0; 3],
            allocation: alloc, return_assumptions: ra,
            num_paths: 2, current_age: 35, seed: Some(0),
        });
        assert_eq!(out.by_age[0].age, 35);
        assert_eq!(out.by_age[1].age, 36);
        assert_eq!(out.by_age[3].age, 38);
    }
}
