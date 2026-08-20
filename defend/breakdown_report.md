# Gate vs ML Detector Breakdown

Evaluated on 300 simulated fraud attacks.

| Defense Result | Count | Percentage |
|---|---:|---:|
| Gate caught | 300 | 100.0% |
| Detector caught | 300 | 100.0% |
| Both caught | 300 | 100.0% |
| Missed | 0 | 0.0% |
| Combined defense | 300 | 100.0% |

The deterministic gate catches high-confidence provenance risks. The ML detector catches
subtle behavioral fraud that rules alone miss. Combined defense is stronger than either
layer alone.
