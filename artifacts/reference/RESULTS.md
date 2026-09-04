# Measured reference results

## Averaged model

| Scenario | Controller | THD₂–₄₀ [%] | Steady RMSE [V] | Recovery [ms] |
|---|---|---:|---:|---:|
| nominal | Cascaded PI | 0.000 | 0.872 | 20.00 |
| nominal | SMC | 0.000 | 0.047 | 20.00 |
| nominal | Adaptive SMC | 0.000 | 0.047 | 20.00 |
| nominal | MPC | 0.000 | 0.018 | 20.00 |
| load-step | Cascaded PI | 0.000 | 2.383 | 20.00 |
| load-step | SMC | 0.000 | 1.116 | 20.00 |
| load-step | Adaptive SMC | 0.010 | 1.857 | 20.00 |
| load-step | MPC | 0.000 | 0.702 | 20.00 |
| dc-sag | Cascaded PI | 0.000 | 0.872 | 20.00 |
| dc-sag | SMC | 0.000 | 0.047 | 20.00 |
| dc-sag | Adaptive SMC | 0.000 | 0.047 | 20.00 |
| dc-sag | MPC | 0.000 | 0.018 | 20.00 |
| noise | Cascaded PI | 0.024 | 0.895 | 20.00 |
| noise | SMC | 0.027 | 0.147 | 20.00 |
| noise | Adaptive SMC | 0.025 | 0.146 | 20.00 |
| noise | MPC | 0.036 | 0.202 | 20.00 |
| mismatch | Cascaded PI | 0.000 | 1.136 | 20.00 |
| mismatch | SMC | 0.000 | 2.720 | 20.00 |
| mismatch | Adaptive SMC | 0.002 | 3.344 | 20.00 |
| mismatch | MPC | 0.000 | 1.571 | 20.00 |
| delay | Cascaded PI | 0.000 | 2.759 | 20.00 |
| delay | SMC | 0.000 | 1.404 | 20.00 |
| delay | Adaptive SMC | 0.003 | 1.889 | 20.00 |
| delay | MPC | 0.000 | 0.879 | 20.00 |
| nonlinear | Cascaded PI | 3.152 | 7.619 | not settled |
| nonlinear | SMC | 2.470 | 5.909 | not settled |
| nonlinear | Adaptive SMC | 1.627 | 3.872 | 20.00 |
| nonlinear | MPC | 1.058 | 2.510 | 20.00 |
| combined | Cascaded PI | 0.025 | 2.845 | 20.00 |
| combined | SMC | 0.031 | 0.333 | 20.00 |
| combined | Adaptive SMC | 0.032 | 0.719 | 20.00 |
| combined | MPC | 0.055 | 0.494 | 20.00 |

## Switching model

| Scenario | Controller | THD₂–₄₀ [%] | Steady RMSE [V] | Recovery [ms] |
|---|---|---:|---:|---:|
| nominal | Cascaded PI | 0.002 | 0.812 | 20.00 |
| nominal | SMC | 0.004 | 0.076 | 20.00 |
| nominal | Adaptive SMC | 0.008 | 0.080 | 20.00 |
| nominal | MPC | 0.007 | 0.076 | 20.00 |
| nonlinear | Cascaded PI | 3.159 | 7.622 | not settled |
| nonlinear | SMC | 2.480 | 5.942 | not settled |
| nonlinear | Adaptive SMC | 1.619 | 3.847 | 20.00 |
| nonlinear | MPC | 1.061 | 2.516 | 20.00 |
