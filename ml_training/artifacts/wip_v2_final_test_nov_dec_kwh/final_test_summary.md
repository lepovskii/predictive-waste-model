# Final Test Summary

## Dataset

- Train period: 2023-01-23 sampai 2025-10-30
- Test period: 2025-11-17 sampai 2025-12-06
- Test rows: 24

## Final Test Metrics

| Metric | Model | Baseline Mean | Baseline Median |
|---|---:|---:|---:|
| RMSE | 196.8050 | 194.4589 | 219.8229 |
| MAE | 124.5188 | 136.1995 | 149.3900 |
| R2 | -0.1058 | -0.0796 | -0.3795 |

## Interpretation

- Berdasarkan MAE, model mengungguli baseline mean Jan-Oct.
- Berdasarkan MAE, model mengungguli baseline median Jan-Oct.
- Hasil ini merupakan final test pada data Nov-Dec yang tidak digunakan saat training/tuning.
- Setelah hasil ini keluar, jangan tuning ulang menggunakan Nov-Dec agar evaluasi tetap jujur.

## Largest Errors

| Date | Profile | Actual WIP | Predicted WIP | Absolute Error |
|---|---|---:|---:|---:|
| 2025-12-03 | IWF 250x125 | 863.7400 | 143.3351 | 720.4049 |
| 2025-12-04 | IWF 200x100 | 464.2300 | 107.5959 | 356.6341 |
| 2025-11-19 | IWF 300x150 | 382.5000 | 138.9880 | 243.5120 |
| 2025-11-18 | IWF 300x150 | 364.6500 | 153.7235 | 210.9265 |
| 2025-11-22 | HB 175x175 | 289.4300 | 106.3726 | 183.0574 |
| 2025-11-29 | HB 150x150 | 278.7800 | 100.7598 | 178.0202 |
| 2025-12-06 | UNP 150x75 | 265.6100 | 110.0239 | 155.5861 |
| 2025-12-02 | L 150x150x15 | 233.4000 | 88.6354 | 144.7646 |
| 2025-11-21 | IWF 150x75 | 198.7400 | 75.8462 | 122.8938 |
| 2025-11-20 | IWF 150x75 | 196.7300 | 74.6349 | 122.0951 |