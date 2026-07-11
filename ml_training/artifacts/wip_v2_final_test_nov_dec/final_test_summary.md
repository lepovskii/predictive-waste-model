# Final Test Summary

## Dataset

- Train period: 2023-01-23 sampai 2025-10-30
- Test period: 2025-11-17 sampai 2025-12-06
- Test rows: 24

## Final Test Metrics

| Metric | Model | Baseline Mean | Baseline Median |
|---|---:|---:|---:|
| RMSE | 218.9115 | 194.4589 | 219.8229 |
| MAE | 143.1982 | 136.1995 | 149.3900 |
| R2 | -0.3681 | -0.0796 | -0.3795 |

## Interpretation

- Berdasarkan MAE, model belum mengungguli baseline mean Jan-Oct.
- Berdasarkan MAE, model mengungguli baseline median Jan-Oct.
- Hasil ini merupakan final test pada data Nov-Dec yang tidak digunakan saat training/tuning.
- Setelah hasil ini keluar, jangan tuning ulang menggunakan Nov-Dec agar evaluasi tetap jujur.

## Largest Errors

| Date | Profile | Actual WIP | Predicted WIP | Absolute Error |
|---|---|---:|---:|---:|
| 2025-12-03 | IWF 250x125 | 863.7400 | 98.2309 | 765.5091 |
| 2025-12-04 | IWF 200x100 | 464.2300 | 78.3801 | 385.8499 |
| 2025-11-19 | IWF 300x150 | 382.5000 | 94.8256 | 287.6744 |
| 2025-11-18 | IWF 300x150 | 364.6500 | 102.7705 | 261.8795 |
| 2025-11-22 | HB 175x175 | 289.4300 | 75.1012 | 214.3288 |
| 2025-11-29 | HB 150x150 | 278.7800 | 65.3486 | 213.4314 |
| 2025-12-06 | UNP 150x75 | 265.6100 | 78.8778 | 186.7322 |
| 2025-12-02 | L 150x150x15 | 233.4000 | 63.0337 | 170.3663 |
| 2025-11-21 | IWF 150x75 | 198.7400 | 49.4988 | 149.2412 |
| 2025-11-20 | IWF 150x75 | 196.7300 | 48.8043 | 147.9257 |