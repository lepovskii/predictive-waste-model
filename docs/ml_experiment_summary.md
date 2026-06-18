# ML Experiment Summary

_Last updated: 2026-06-05_

## Objective

The machine learning objective is to predict:

```text
wip_ton
```

WIP is treated as a production quality indicator because it represents steel products that are not yet considered prime and may require additional handling, rework, or further inspection.

The model is **not positioned as a decision support system**. It is used as a prediction component inside the production quality monitoring system.

---

## Target Definition

Target variable:

```text
wip_ton
```

Target meaning:

| Target | Meaning |
|---|---|
| `wip_ton` | Estimated tonnage of WIP product for each production profile |

The prediction is made at:

```text
profile-level production data
```

The daily total WIP is calculated by summing profile-level predictions.

---

## Dataset Strategy

The dataset was split chronologically to reduce data leakage and simulate future prediction behavior.

| Period | Usage |
|---|---|
| Jan-Aug | Initial model comparison and training |
| September | Holdout validation and hyperparameter tuning |
| Jan-Oct | Final training |
| Nov-Dec | Final testing |

This split ensures that the final test data comes after the training period.

Final training dataset:

```text
ml_training/dataset_completed - super_final_jan_oct.csv
```

Final testing dataset:

```text
ml_training/dataset_completed - nov_dec_dataset.csv
```

---

## Dataset Cleaning Decisions

The original company dataset contained several issues:

```text
merged cells
zero-heavy columns
threshold variables
output-related variables
month-to-month column variation
potential leakage variables
```

The dataset used for training was normalized before model development.

Important cleaning decisions:

| Issue | Decision |
|---|---|
| Merged daily values | Allocated into profile-level rows |
| Shutdown rows | Removed from model training/testing |
| Production zero rows | Removed from model training/testing |
| Unverified WIP zero anomaly | Removed from final training |
| Missing numeric process values | Rechecked and filled only when semantically valid |
| Date format | Standardized to `YYYY-MM-DD` |
| Profile name | Normalized as clean text |

---

## Leakage Prevention

The following variables were not used as model input features because they are output-related or could leak target information:

```text
transfer_to_warehouse_ton
class_b_ton
reject_ton
miss_roll_ton
dispatch_total
stock_total
wip_percentage
reject_percentage
miss_roll_percentage
class_b_percentage
```

Reason:

These variables represent actual production output, quality outcome, or post-production result. Including them as features would make the model learn from information that should not be available at prediction time.

---

## Final Feature Set

The final model uses 25 input columns:

```text
profile_name
raw_material_ton
production_ton
material_pcs
production_pcs
total_hrs
availables_hrs
setup_time
program_stop_min
stand_change
production_stop_min
mechanic_stop_min
electric_stop_min
roll_shop_stop_min
test_rolling_stop_min
trial_rolling_stop_min
others_stop_min
downtime_total_min
rolling_hot_hrs
idle_hrs
rolling_hrs
gas_total_day_nm3
kv_20
kv_33
electricity_total_kwh
```

Feature categories:

| Category | Features |
|---|---|
| Profile identity | `profile_name` |
| Production volume | `raw_material_ton`, `production_ton`, `material_pcs`, `production_pcs` |
| Time availability | `total_hrs`, `availables_hrs`, `rolling_hot_hrs`, `idle_hrs`, `rolling_hrs` |
| Downtime | `setup_time`, `program_stop_min`, `stand_change`, `production_stop_min`, `mechanic_stop_min`, `electric_stop_min`, `roll_shop_stop_min`, `test_rolling_stop_min`, `trial_rolling_stop_min`, `others_stop_min`, `downtime_total_min` |
| Energy consumption | `gas_total_day_nm3`, `kv_20`, `kv_33`, `electricity_total_kwh` |

---

## Candidate Models

The following regression models were compared:

```text
Decision Tree
Random Forest
Extra Trees
Gradient Boosting
XGBoost
```

XGBoost was included because it is a strong gradient boosting model and was part of the model candidate experiment.

---

## Initial Findings

Early experiments showed that predicting WIP is more difficult than predicting prime output.

Key reasons:

```text
WIP is more irregular than transfer to warehouse.
WIP depends on quality and operational factors that may not be fully captured in the management dataset.
WIP contains extreme values.
The dataset size is limited.
```

This is why simple model comparison and baseline comparison were necessary before deciding the final artifact.

---

## Dataset Variant Experiments

Several dataset variants were tested:

| Dataset Variant | Purpose |
|---|---|
| `dataset_clean.csv` | Main clean dataset with process and downtime features |
| `dataset_clean_no_downtime.csv` | Tested whether sparse downtime detail should be removed |
| `dataset_clean_with_ratios.csv` | Tested whether ratio features improve prediction |
| `super_final_jan_oct.csv` | Final training dataset |

Main conclusion:

```text
The clean dataset with process and downtime features was preferred.
```

The ratio-enhanced dataset did not improve the final direction enough to replace the clean feature set.

---

## September Candidate Validation

On September validation data, the best candidate before tuning was Extra Trees.

| Model | RMSE | MAE | R2 |
|---|---:|---:|---:|
| Extra Trees | 115.25 | 83.49 | -0.041 |
| Random Forest | 115.72 | 89.88 | -0.049 |
| XGBoost | 128.33 | 103.57 | -0.291 |
| Gradient Boosting | 137.09 | 107.05 | -0.473 |
| Decision Tree | 186.19 | 125.41 | -1.717 |

Baseline comparison:

| Baseline | RMSE | MAE | R2 |
|---|---:|---:|---:|
| Mean Jan-Aug | 117.11 | 89.39 | -0.075 |
| Median Jan-Aug | 113.12 | 76.14 | -0.003 |

Interpretation:

Extra Trees outperformed the mean baseline but still did not outperform the median baseline by MAE at this stage.

---

## Hyperparameter Tuning

The following models were tuned:

```text
Extra Trees
Random Forest
XGBoost
```

Best tuned model:

```text
ExtraTreesRegressor
```

Best parameters:

```json
{
  "n_estimators": 300,
  "max_depth": 4,
  "min_samples_leaf": 1,
  "max_features": 0.7,
  "bootstrap": true
}
```

Tuning result on September:

| Model | RMSE | MAE | R2 |
|---|---:|---:|---:|
| Extra Trees | 102.85 | 78.07 | 0.171 |
| Random Forest | 110.04 | 81.26 | 0.051 |
| XGBoost | 114.76 | 88.33 | -0.032 |

Interpretation:

Extra Trees became the strongest model after tuning.

XGBoost improved after tuning but remained weaker than Extra Trees on this dataset.

Possible explanation:

```text
The dataset is relatively small.
The target is noisy.
The data is profile-dependent.
Extra Trees is more stable under noisy tabular conditions.
```

---

## Final Model Selection

The selected final model is:

```text
ExtraTreesRegressor
```

The final model artifact is:

```text
ml_training/artifacts/wip_final_jan_oct_extra_trees/pipeline.pkl
```

The final artifact was selected because:

```text
It performed best during tuning.
It outperformed baselines on final testing.
It was more stable than XGBoost for the available dataset.
It supports feature importance analysis.
```

---

## Final Training

The final model was trained using Jan-Oct data:

```text
ml_training/dataset_completed - super_final_jan_oct.csv
```

Rows used:

```text
115
```

Target summary:

| Statistic | Value |
|---|---:|
| Min | 0.37 |
| Max | 713.53 |
| Mean | 126.12 |
| Median | 89.49 |
| Std | 132.84 |

Final training artifact folder:

```text
ml_training/artifacts/wip_final_jan_oct_extra_trees/
```

Important files:

```text
pipeline.pkl
model_metadata.json
feature_importance.csv
train_predictions_diagnostic.csv
```

---

## Final Test

The final test was performed using untouched Nov-Dec data:

```text
ml_training/dataset_completed - nov_dec_dataset.csv
```

Rows used:

```text
24
```

Target summary:

| Statistic | Value |
|---|---:|
| Min | 0.22 |
| Max | 863.74 |
| Mean | 199.36 |
| Median | 195.43 |
| Std | 191.18 |

Final test artifact folder:

```text
ml_training/artifacts/wip_final_test_nov_dec/
```

Important files:

```text
final_test_metrics.json
final_test_predictions.csv
final_test_summary.md
```

---

## Final Test Result

| Metric | Model | Baseline Mean | Baseline Median |
|---|---:|---:|---:|
| RMSE | 177.37 | 200.97 | 217.02 |
| MAE | 110.00 | 139.61 | 147.58 |
| R2 | 0.102 | -0.153 | -0.345 |

Interpretation:

The final model outperformed both mean and median baselines on RMSE, MAE, and R2.

This indicates that the model learned useful patterns from the production process features instead of only predicting a central tendency.

---

## Monthly Final Test Result

| Month | RMSE | MAE | R2 |
|---|---:|---:|---:|
| November | 99.51 | 82.56 | 0.367 |
| December | 289.51 | 176.62 | -0.443 |

Interpretation:

The model performed better in November than in December.

December contained higher WIP values and more extreme cases, which made prediction more difficult.

---

## Largest Final Test Errors

| Date | Profile | Actual WIP | Predicted WIP | Absolute Error |
|---|---|---:|---:|---:|
| 2025-12-03 | IWF 250x125 | 863.74 | 176.87 | 686.87 |
| 2025-12-04 | IWF 200x100 | 464.23 | 159.12 | 305.11 |
| 2025-11-19 | IWF 300x150 | 382.50 | 161.79 | 220.71 |
| 2025-11-18 | IWF 300x150 | 364.65 | 203.81 | 160.84 |

Interpretation:

The model tends to underpredict extreme WIP values.

This is the main limitation of the current artifact.

---

## Feature Importance

Feature importance is available at:

```text
ml_training/artifacts/wip_final_jan_oct_extra_trees/feature_importance.csv
```

Top important features during final training included:

```text
setup_time
rolling_hrs
kv_33
electricity_total_kwh
production_ton
gas_total_day_nm3
raw_material_ton
profile_name_IWF 250x125
kv_20
idle_hrs
rolling_hot_hrs
```

Interpretation:

The model uses a combination of setup time, production volume, energy consumption, rolling time, and profile identity.

This supports the idea that WIP prediction is influenced by both production volume and process-related signals.

---

## Key Finding

The final model is usable as a first-version artifact because it outperforms simple baseline methods on untouched final test data.

However, it should not be claimed as highly accurate for extreme WIP cases.

Safe conclusion:

```text
The Extra Trees model can estimate WIP better than mean and median baselines, but its performance decreases on extreme WIP cases. Future improvement requires more representative historical data, especially cases with high WIP values.
```

---

## Artifact References

Model selection and tuning:

```text
ml_training/artifacts/wip_sep_candidate_validation/
ml_training/artifacts/wip_sep_tuning/
```

Final training:

```text
ml_training/artifacts/wip_final_jan_oct_extra_trees/
```

Final testing:

```text
ml_training/artifacts/wip_final_test_nov_dec/
```

Important files:

```text
ml_training/artifacts/wip_final_jan_oct_extra_trees/pipeline.pkl
ml_training/artifacts/wip_final_jan_oct_extra_trees/model_metadata.json
ml_training/artifacts/wip_final_jan_oct_extra_trees/feature_importance.csv
ml_training/artifacts/wip_final_test_nov_dec/final_test_metrics.json
ml_training/artifacts/wip_final_test_nov_dec/final_test_predictions.csv
ml_training/artifacts/wip_final_test_nov_dec/final_test_summary.md
```

---

## Limitations

Current ML limitations:

```text
Dataset size is limited.
WIP is influenced by operational and quality factors that may not be fully captured in the management report dataset.
Extreme WIP values are difficult to predict.
The model tends to underpredict high WIP cases.
The model only predicts WIP, not reject, class B, miss roll, or transfer to warehouse.
The current model expects normalized input features, not raw merged-cell CSV files.
```

---

## Future Improvement

Possible future improvements:

```text
Add more historical months.
Add more high-WIP cases.
Add machine-level process variables if available.
Improve CSV adapter layer.
Monitor prediction drift after reconciliation.
Retrain model when enough new actual data is collected.
```

Most important improvement direction:

```text
Add more representative data, especially data containing high WIP cases.
```

---

## Summary

Final selected artifact:

```text
ml_training/artifacts/wip_final_jan_oct_extra_trees/pipeline.pkl
```

Final test performance:

```text
RMSE = 177.37
MAE = 110.00
R2 = 0.102
```

Final conclusion:

```text
The model is suitable as an initial prediction artifact for the system, but future retraining is recommended when additional production data becomes available.
```