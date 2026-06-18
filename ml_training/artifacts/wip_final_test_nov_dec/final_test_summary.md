# Final Test Summary

## Dataset

- Train period: 2025-01-22 sampai 2025-10-30
- Test period: 2025-11-17 sampai 2025-12-06
- Test rows: 24

## Final Test Metrics

| Metric | Model | Baseline Mean | Baseline Median |
|---|---:|---:|---:|
| RMSE | 177.3689 | 200.9748 | 217.0215 |
| MAE | 109.9962 | 139.6071 | 147.5783 |
| R2 | 0.1019 | -0.1531 | -0.3446 |

## Interpretation

- Berdasarkan MAE, model mengungguli baseline mean Jan-Oct.
- Berdasarkan MAE, model mengungguli baseline median Jan-Oct.
- Hasil ini merupakan final test pada data Nov-Dec yang tidak digunakan saat training/tuning.
- Setelah hasil ini keluar, jangan tuning ulang menggunakan Nov-Dec agar evaluasi tetap jujur.

## Largest Errors

| Date | Profile | Actual WIP | Predicted WIP | Absolute Error |
|---|---|---:|---:|---:|
| 2025-12-03 | IWF 250x125 | 863.7400 | 176.8680 | 686.8720 |
| 2025-12-04 | IWF 200x100 | 464.2300 | 159.1152 | 305.1148 |
| 2025-11-19 | IWF 300x150 | 382.5000 | 161.7912 | 220.7088 |
| 2025-11-18 | IWF 300x150 | 364.6500 | 203.8102 | 160.8398 |
| 2025-11-22 | HB 175x175 | 289.4300 | 158.3356 | 131.0944 |
| 2025-11-29 | HB 150x150 | 278.7800 | 150.8649 | 127.9151 |
| 2025-11-28 | HB 100x100 | 29.9100 | 155.5799 | 125.6699 |
| 2025-11-26 | IWF 200x100 | 66.3500 | 176.2927 | 109.9427 |
| 2025-12-02 | L 150x150x15 | 233.4000 | 127.8573 | 105.5427 |
| 2025-12-06 | UNP 150x75 | 265.6100 | 365.3237 | 99.7137 |