# ML Experiment Summary

_Last updated: 2026-06-25_

## Objective

The machine learning objective in this project is to predict:

```text
wip_ton
```

WIP is treated as a production quality indicator because it represents steel products that are not yet considered prime and may require additional handling, rework, reforming, refining, or further inspection before being classified into a final quality category.

The model is **not positioned as a decision support system**. It is positioned as a prediction component inside a production quality monitoring system.

The main research contribution is not only the regression model, but the full software system that connects:

```text
normalized production data -> ML inference artifact -> API -> database -> async worker -> frontend -> reconciliation flow
```

The prediction model is therefore evaluated as an important component, while the system architecture remains the main implementation focus.

---

## Prediction Timing

The prediction is made after daily production process data is available, but before final WIP actual values are reconciled into the system.

This means the model is allowed to use process features such as:

```text
production_ton
downtime details
rolling hours
gas consumption
electricity consumption
stand change
trial rolling
test rolling
```

These features are considered valid because they describe the production process and are not direct quality outcome labels.

The model is **not** intended to predict WIP before production starts.

Safe interpretation:

```text
The model estimates WIP based on completed daily production process signals, before final quality reconciliation is entered into the system.
```

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

The prediction grain is:

```text
one row per production_date + profile_name
```

The daily total WIP is calculated by summing profile-level predictions.

---

## Dataset Source Condition

The source data comes from historical production reports prepared in spreadsheet form. The raw data was not originally designed as a machine-learning dataset.

Important source-data characteristics:

```text
merged cells
multi-profile production days
month-to-month column variation
zero-heavy columns
threshold columns
output-related columns
mixed date formats
mixed numeric formats
inconsistent historical report structures
```

Because of these conditions, the dataset required manual-assisted preprocessing before model training.

---

## Manual-Assisted Preprocessing Methodology

The training dataset was prepared using a **manual-assisted preprocessing** approach.

This means the dataset was not edited arbitrarily. Cleaning decisions were made using documented rules, domain interpretation, and validation checks.

Academic framing:

```text
The original company reports were not structured transaction tables. Therefore, preprocessing required a combination of technical normalization, domain-based interpretation, and manual validation to produce a reliable profile-level dataset for supervised learning.
```

This is different from simply editing a CSV manually. The manual work is treated as a controlled data preparation process.

---

## Preprocessing Stages

The preprocessing workflow can be described in six stages:

| Stage | Purpose |
|---|---|
| Data understanding | Identify target, process features, output columns, threshold columns, and leakage risk |
| Data cleaning | Fix date format, numeric format, missing values, shutdown rows, and invalid production rows |
| Data consolidation | Merge monthly data into one consistent training table |
| Granularity normalization | Convert daily/profile data into one row per `production_date + profile_name` |
| Feature selection | Keep process features and remove output/leakage variables |
| Data validation | Check missing values, duplicate keys, outliers, unit consistency, and target consistency |

---

## Dataset Cleaning Decisions

Important cleaning decisions:

| Issue | Decision | Reason |
|---|---|---|
| Merged daily values | Allocated into profile-level rows | The model and database use profile-level grain |
| Shutdown rows | Removed | Shutdown does not represent normal production behavior |
| Production zero rows | Removed | The target relationship is not meaningful without production |
| Date format | Standardized to `YYYY-MM-DD` | Required for chronological split and database consistency |
| Profile name | Trimmed and cleaned as text | Required for categorical encoding and unique key consistency |
| Numeric separators | Standardized before training | Spreadsheet exports used mixed comma/dot formats |
| Output quality columns | Removed from input features | Prevent target leakage |
| Threshold columns | Removed from input features | Thresholds can change by era and may not represent process behavior |
| WIP actual | Kept only as target | Required for supervised learning |

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

These variables represent actual production output, final quality outcome, or post-production result. Including them as input features would make the model learn from information that should not be available at prediction time.

Important distinction:

| Feature Type | Used as Input? | Reason |
|---|---:|---|
| Process features | Yes | Known from the production process |
| Energy consumption | Yes | Process signal, not final quality label |
| Downtime details | Yes | Process signal, not final quality label |
| WIP actual | No | Target variable |
| Reject/Class B/Miss Roll | No | Final quality outcome |
| Transfer to Warehouse | No | Finish-good outcome |

---

## Dataset Split Strategy

The dataset was split chronologically to reduce leakage and simulate future prediction behavior.

| Period | Usage |
|---|---|
| Jan-Aug 2025 | Initial model comparison and training |
| September 2025 | Holdout validation and hyperparameter tuning |
| Jan-Oct 2025 | Final v1 training |
| Nov-Dec 2025 | Final testing |

This split ensures that the final test data comes after the training period.

Final v1 training dataset:

```text
ml_training/dataset_completed - super_final_jan_oct.csv
```

Final testing dataset:

```text
ml_training/dataset_completed - nov_dec_dataset.csv
```

---

## Model Feature Contract

The system separates two concepts:

| Contract | Meaning |
|---|---|
| Application data contract | The API/database can store rich production process data |
| Model feature contract | Each model artifact declares which features it actually uses |

This separation allows model artifacts to be replaced as long as the inference layer can map the available production payload into the features expected by the model.

Important statement:

```text
The system can support model replacement without redesigning the whole application, as long as the replacement artifact follows a compatible input-output inference contract.
```

This should not be overstated as "no change at all". If a future model requires different or new features, the adapter/inference layer may need adjustment.

---

## v1 Feature Set

The validated production artifact is v1. It uses the current 2025 report format and keeps the richer process feature set.

The v1 model uses 25 input columns:

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
| Downtime and process condition | `setup_time`, `program_stop_min`, `stand_change`, `production_stop_min`, `mechanic_stop_min`, `electric_stop_min`, `roll_shop_stop_min`, `test_rolling_stop_min`, `trial_rolling_stop_min`, `others_stop_min`, `downtime_total_min` |
| Energy consumption | `gas_total_day_nm3`, `kv_20`, `kv_33`, `electricity_total_kwh` |

Rationale:

```text
The v1 model uses the latest and most operationally relevant 2025 production report format. These process features are available before final WIP reconciliation and do not directly contain the target outcome.
```

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

XGBoost was included because it is a strong gradient boosting model and was part of the candidate experiment.

---

## Initial Modeling Findings

Early experiments showed that predicting WIP is more difficult than predicting prime output.

Key reasons:

```text
WIP is more irregular than transfer to warehouse.
WIP depends on quality and operational factors that may not be fully captured in the management dataset.
WIP contains extreme values.
The dataset size is limited.
Some high-WIP events are rare and difficult to generalize.
```

This is why model comparison and baseline comparison were necessary before deciding the final artifact.

---

## Dataset Variant Experiments

Several dataset variants were tested:

| Dataset Variant | Purpose |
|---|---|
| `dataset_clean.csv` | Main clean dataset with process and downtime features |
| `dataset_clean_no_downtime.csv` | Tested whether sparse downtime detail should be removed |
| `dataset_clean_with_ratios.csv` | Tested whether ratio features improve prediction |
| `super_final_jan_oct.csv` | Final v1 training dataset |

Main conclusion:

```text
The clean dataset with process and downtime features was preferred.
```

The ratio-enhanced dataset did not improve the final direction enough to replace the clean process feature set.

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

Best parameters for v1:

```json
{
  "n_estimators": 300,
  "max_depth": 4,
  "min_samples_leaf": 1,
  "max_features": 0.7,
  "bootstrap": true,
  "random_state": 42
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

## v1 Final Model Selection

The selected v1 model is:

```text
ExtraTreesRegressor
```

The final v1 model artifact is:

```text
ml_training/artifacts/wip_final_jan_oct_extra_trees/pipeline.pkl
```

The final artifact was selected because:

```text
It performed best during tuning.
It outperformed baselines on final testing.
It was more stable than XGBoost for the available dataset.
It supports feature importance analysis.
It uses the latest operational report feature set.
```

---

## v1 Final Training

The final v1 model was trained using Jan-Oct 2025 data:

```text
ml_training/dataset_completed - super_final_jan_oct.csv
```

Rows used:

```text
115
```

Training period:

```text
2025-01-22 to 2025-10-30
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

## v1 Final Test

The final test was performed using untouched Nov-Dec 2025 data:

```text
ml_training/dataset_completed - nov_dec_dataset.csv
```

Rows used:

```text
24
```

Testing period:

```text
2025-11-17 to 2025-12-06
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

## v1 Final Test Result

| Metric | Model | Baseline Mean | Baseline Median |
|---|---:|---:|---:|
| RMSE | 177.37 | 200.97 | 217.02 |
| MAE | 110.00 | 139.61 | 147.58 |
| R2 | 0.102 | -0.153 | -0.345 |

Interpretation:

The v1 model outperformed both mean and median baselines on RMSE, MAE, and R2.

This indicates that the model learned useful patterns from production process features instead of only predicting a central tendency.

---

## v1 Monthly Final Test Result

| Month | RMSE | MAE | R2 |
|---|---:|---:|---:|
| November | 99.51 | 82.56 | 0.367 |
| December | 289.51 | 176.62 | -0.443 |

Interpretation:

The model performed better in November than in December.

December contained higher WIP values and more extreme cases, which made prediction more difficult.

---

## Largest v1 Final Test Errors

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

## v1 Feature Importance

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

## v1 Key Finding

The v1 model is usable as the first validated artifact because it outperforms simple baseline methods on untouched final test data.

However, it should not be claimed as highly accurate for extreme WIP cases.

Safe conclusion:

```text
The Extra Trees v1 model can estimate WIP better than mean and median baselines, but its performance decreases on extreme WIP cases. Future improvement requires more representative historical data, especially cases with high WIP values.
```

---

## Cross-Year Dataset v2 Motivation

After the v1 model artifact was completed, additional historical production data from 2023 and 2024 became available.

The purpose of v2 was to test whether adding more historical data could improve model performance.

Candidate v2 training dataset:

```text
ml_training/dataset_completed - cross_year_datasets_best_final.csv
```

Dataset range:

| Year | Rows |
|---|---:|
| 2023 | 68 |
| 2024 | 87 |
| 2025 Jan-Oct | 115 |

Total rows:

```text
270
```

The previous v1 Jan-Oct 2025 final training dataset had 115 rows. The cross-year dataset increased the amount of training data, but it also introduced historical format differences.

---

## Cross-Year Data Consolidation Issues

The historical reports were not immediately compatible with the 2025 training format. Several issues were caused by genuine differences in the company's reporting format, not by modeling code.

Important source-data issues:

| Issue | Explanation | Decision |
|---|---|---|
| Different report eras | The 2023 and early 2024 reports used an older format, while the newer 2025-like format started around mid-2024 | Use only stable cross-format columns |
| `Prod Std` vs `Prod Act` | Older reports contained both standard and actual production values | Use actual production as `production_ton` |
| Delay in hours | Older reports used delay/hour-style values instead of detailed downtime minutes | Convert downtime-related columns to minutes |
| Missing detailed downtime categories | Some 2025 downtime features did not exist in 2023/2024 | Drop features that are not consistently available across years |
| Multi-profile daily rows | Some old reports combined more than one profile in a single production row | Use only rows that can be represented at profile-level grain |
| Trial/status rows | Some rows had operational status notes such as trial in the original Excel files | Keep only rows judged valid as actual production records |
| Decimal and thousand separators | Values used mixed formats such as decimal comma, thousand dot, or spreadsheet-formatted numbers | Normalize numeric values before training |
| Date/profile grain | The database and model expect one row per `production_date + profile_name` | Remove or aggregate duplicate keys before training |
| Output/leakage variables | Quality outcome and finish-good columns were present in raw reports | Exclude leakage columns from features |
| Profile spelling/case variation | Some profile names differ by capitalization or trailing spaces | Preserve business names but strip accidental whitespace in training code |

This consolidation was one of the most difficult parts of the ML workflow because the dataset was a management production report, not a machine-learning-ready dataset.

---

## v2 Cleaning Audit Note

During manual preparation of the cross-year dataset, several temporary cleaning mistakes were identified and corrected before selecting the final v2 dataset.

These late-stage mistakes were caused by the manual normalization process, not by the original company report itself.

Corrected preparation mistakes included:

```text
decimal separator conversion mistakes
some 2025 values accidentally shifted or scaled during spreadsheet cleanup
temporary duplicate production_date + profile_name key
temporary extra helper column total_electric_sim
temporary electricity and gas consistency mismatches after manual edits
```

The final accepted v2 dataset is:

```text
ml_training/dataset_completed - cross_year_datasets_best_final.csv
```

Validation summary for the accepted v2 dataset:

| Check | Result |
|---|---:|
| Rows | 270 |
| Columns | 21 |
| Missing numeric values | 0 |
| Duplicate `production_date + profile_name` | 0 |
| `production_ton <= 0` | 0 |
| `wip_ton <= 0` | 0 |
| `wip_ton > production_ton` | 0 |
| `production_ton > raw_material_ton * 1.05` | 0 |
| Gas consistency issue | 0 |

Remaining non-blocking notes:

```text
Some production rows are very small, but they are retained because they represent actual production.
Profile names are preserved as company-reported values, while training code still trims accidental whitespace.
```

---

## v2 Cross-Year Feature Set

For the v2 cross-year model, the feature set was reduced to columns that are consistently available across 2023, 2024, and 2025.

The v2 model uses 19 input columns:

```text
profile_name
raw_material_ton
production_ton
material_pcs
production_pcs
availables_hrs
production_stop_min
mechanic_stop_min
electric_stop_min
roll_shop_stop_min
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

Removed from v2 because they are not stable across report eras:

```text
total_hrs
setup_time
program_stop_min
stand_change
test_rolling_stop_min
trial_rolling_stop_min
```

Reason:

The v2 model should not fill unavailable historical process features with fake zeros because that would introduce artificial patterns. Using the intersection of reliable cross-year features is more defensible for cross-year experimentation.

Important distinction:

```text
v1 uses the richer current-format feature set for operational deployment.
v2 uses the reduced cross-year feature set for historical retraining experimentation.
```

---

## v2 Model Comparison

The v2 cross-year dataset was evaluated using time-series cross-validation before replacing the v1 artifact.

Dataset:

```text
ml_training/dataset_completed - cross_year_datasets_best_final.csv
```

Rows used:

```text
270
```

Two target strategies were compared:

```text
none
log1p
```

### v2 Comparison Without Target Transform

Output folder:

```text
ml_training/artifacts/wip_v2_cross_year_compare_none/
```

| Model | RMSE Mean | MAE Mean | R2 Mean |
|---|---:|---:|---:|
| Random Forest | 145.71 | 108.76 | -0.217 |
| XGBoost | 147.39 | 108.77 | -0.237 |
| Gradient Boosting | 153.78 | 109.62 | -0.301 |
| Extra Trees | 161.96 | 118.93 | -0.497 |
| Decision Tree | 184.52 | 130.29 | -0.926 |

Interpretation:

Without target transformation, Random Forest slightly outperformed XGBoost, while Extra Trees became weaker than expected.

### v2 Comparison With `log1p` Target Transform

Output folder:

```text
ml_training/artifacts/wip_v2_cross_year_compare_log1p/
```

| Model | RMSE Mean | MAE Mean | R2 Mean |
|---|---:|---:|---:|
| Extra Trees | 135.06 | 88.01 | -0.002 |
| Random Forest | 138.04 | 89.20 | -0.003 |
| Gradient Boosting | 136.00 | 90.70 | 0.011 |
| XGBoost | 138.75 | 91.98 | -0.019 |
| Decision Tree | 165.03 | 111.61 | -0.417 |

Baseline during v2 comparison:

| Baseline | RMSE Mean | MAE Mean | R2 Mean |
|---|---:|---:|---:|
| Mean baseline | 155.30 | 127.36 | -0.434 |

Interpretation:

The `log1p` target transform substantially improved model stability during cross-validation. Extra Trees became the best model by MAE, with a mean MAE improvement of approximately 39.35 tons over the mean baseline.

This made the following v2 artifact worth testing:

```text
ExtraTreesRegressor + log1p target transform
```

---

## v2 Training Artifact

The v2 artifact was trained using the cross-year dataset and the best comparison direction:

```text
ExtraTreesRegressor + log1p target transform
```

Artifact folder:

```text
ml_training/artifacts/wip_v2_cross_year_extra_trees_log1p/
```

Main artifact:

```text
ml_training/artifacts/wip_v2_cross_year_extra_trees_log1p/pipeline.pkl
```

Training summary:

| Item | Value |
|---|---|
| Rows used | 270 |
| Date range | 2023-01-23 to 2025-10-30 |
| Target transform | `log1p` |
| Input features | 19 |
| Unique dates | 204 |
| Unique profiles | 30 |

Model parameters:

```json
{
  "n_estimators": 500,
  "max_depth": 5,
  "min_samples_leaf": 3,
  "random_state": 42,
  "n_jobs": -1
}
```

---

## v2 Final Test

The v2 artifact was evaluated on the normalized Nov-Dec 2025 test dataset using the same final test period.

Test dataset:

```text
ml_training/dataset_completed - nov_dec_dataset_kwh.csv
```

Output folder:

```text
ml_training/artifacts/wip_v2_final_test_nov_dec_kwh/
```

Rows used:

```text
24
```

Testing period:

```text
2025-11-17 to 2025-12-06
```

---

## v2 Final Test Result

| Metric | v2 Model | Baseline Mean | Baseline Median |
|---|---:|---:|---:|
| RMSE | 196.80 | 194.46 | 219.82 |
| MAE | 124.52 | 136.20 | 149.39 |
| R2 | -0.106 | -0.080 | -0.380 |

Interpretation:

The v2 model beat the mean baseline by MAE, but it did not beat the mean baseline by RMSE or R2.

Compared with v1, v2 was weaker on the final Nov-Dec test.

---

## v1 vs v2 Final Test Comparison

| Artifact | Training Data | Input Features | RMSE | MAE | R2 | Decision |
|---|---|---:|---:|---:|---:|---|
| v1 Extra Trees | Jan-Oct 2025 | 25 | 177.37 | 110.00 | 0.102 | Keep as main artifact |
| v2 Extra Trees + log1p | 2023-Oct 2025 | 19 | 196.80 | 124.52 | -0.106 | Keep as experiment |

Interpretation:

Adding more historical data did not automatically improve final test performance.

The likely reasons are:

```text
cross-year report format differences
feature reduction from 25 to 19 columns
older production process distribution shift
more heterogeneous profile distribution
log1p target transform producing conservative predictions
high-WIP final test cases that remain difficult to predict
```

---

## v2 Monthly Final Test Result

| Month | RMSE | MAE | R2 | Actual Mean | Predicted Mean |
|---|---:|---:|---:|---:|---:|
| November | 113.38 | 80.61 | 0.178 | 145.63 | 82.84 |
| December | 318.71 | 231.15 | -0.749 | 329.83 | 98.68 |

Interpretation:

The v2 model strongly underpredicted the WIP level in December.

This suggests that the cross-year artifact became more conservative and failed to capture high-WIP spikes in the final test period.

---

## Largest v2 Final Test Errors

| Date | Profile | Actual WIP | Predicted WIP | Absolute Error |
|---|---|---:|---:|---:|
| 2025-12-03 | IWF 250x125 | 863.74 | 143.34 | 720.40 |
| 2025-12-04 | IWF 200x100 | 464.23 | 107.60 | 356.63 |
| 2025-11-19 | IWF 300x150 | 382.50 | 138.99 | 243.51 |
| 2025-11-18 | IWF 300x150 | 364.65 | 153.72 | 210.93 |

Interpretation:

The v2 model underpredicted extreme WIP cases more strongly than v1.

---

## v2 Final Decision

The v2 artifact is not selected as the main system artifact.

Decision:

```text
Keep v1 as the active model artifact.
Use v2 as a documented experiment.
```

Reason:

```text
Although v2 used more historical data, it produced weaker final test performance than v1. The additional data increased coverage but also introduced historical inconsistencies and distribution shift.
```

This supports an important ML lesson:

```text
More data does not always improve model performance when the additional data comes from inconsistent reporting formats or different operational regimes.
```

---

## Optional Future Ablation

A future diagnostic experiment can be performed by training a Jan-Oct 2025-only model using the reduced v2 feature set.

Possible dataset name:

```text
ml_training/dataset_completed - super_final_jan_oct_feature_subset.csv
```

Purpose:

```text
Isolate whether v2 performance dropped mainly because of feature reduction or because of adding 2023/2024 historical data.
```

Possible interpretations:

| Result | Meaning |
|---|---|
| Jan-Oct feature subset remains strong | v2 weakness likely comes from 2023/2024 distribution shift |
| Jan-Oct feature subset drops strongly | v2 weakness likely comes from removing important 2025 process features |
| Jan-Oct feature subset drops slightly | Both feature reduction and cross-year shift may contribute |

Important rule:

```text
This ablation should not use Nov-Dec final test results for tuning decisions, because Nov-Dec has already been used as final evaluation.
```

---

## Active Model Decision

The active model artifact for the system remains:

```text
ml_training/artifacts/wip_final_jan_oct_extra_trees/pipeline.pkl
```

The backend can continue using v1 because:

```text
v1 has the best final test performance.
v1 uses the latest operational report feature set.
v1 is already integrated into the backend inference flow.
v1 follows the current API payload structure.
v1 outperformed mean and median baselines on untouched final test data.
```

v2 is retained as:

```text
cross-year retraining experiment
model replacement candidate evidence
future research direction
```

---

## Connection to Adapter Layer

The manual preprocessing process directly informed the system's CSV adapter layer.

Rules discovered during dataset preparation became the basis for:

```text
schema detection
column normalization
numeric parsing
date parsing
required feature validation
ignored leakage columns
warning and error reporting
payload generation for prediction
```

This connects the ML preparation work to the software system.

Academic framing:

```text
Manual-assisted preprocessing was used to construct the initial supervised learning dataset. The preprocessing rules were then operationalized into an adapter layer so that future user-uploaded production reports can be validated and normalized before inference.
```

---

## System-Level ML Interpretation

The final system should not be presented as a highly accurate universal predictor of WIP.

A safer and stronger statement is:

```text
The system demonstrates how a machine-learning artifact can be integrated into a modular production quality prediction workflow, including input validation, asynchronous inference, database persistence, reconciliation, and model artifact replacement.
```

Accuracy is still evaluated, but the main contribution is the software architecture that makes ML inference operational.

---

## Artifact References

Model selection and tuning:

```text
ml_training/artifacts/wip_sep_candidate_validation/
ml_training/artifacts/wip_sep_tuning/
```

v1 final training:

```text
ml_training/artifacts/wip_final_jan_oct_extra_trees/
```

v1 final testing:

```text
ml_training/artifacts/wip_final_test_nov_dec/
```

v2 model comparison:

```text
ml_training/artifacts/wip_v2_cross_year_compare_none/
ml_training/artifacts/wip_v2_cross_year_compare_log1p/
```

v2 final training:

```text
ml_training/artifacts/wip_v2_cross_year_extra_trees_log1p/
```

v2 final testing:

```text
ml_training/artifacts/wip_v2_final_test_nov_dec_kwh/
```

Important files:

```text
ml_training/artifacts/wip_final_jan_oct_extra_trees/pipeline.pkl
ml_training/artifacts/wip_final_jan_oct_extra_trees/model_metadata.json
ml_training/artifacts/wip_final_jan_oct_extra_trees/feature_importance.csv
ml_training/artifacts/wip_final_test_nov_dec/final_test_metrics.json
ml_training/artifacts/wip_final_test_nov_dec/final_test_predictions.csv
ml_training/artifacts/wip_v2_cross_year_extra_trees_log1p/pipeline.pkl
ml_training/artifacts/wip_v2_final_test_nov_dec_kwh/final_test_metrics.json
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
Cross-year historical data introduces format and distribution inconsistencies.
```

---

## Future Improvement

Possible future improvements:

```text
Add more high-WIP cases.
Add machine-level process variables if available.
Improve CSV adapter layer.
Implement model metadata-based feature validation.
Monitor prediction drift after reconciliation.
Retrain model when enough new actual data is collected.
Run controlled feature-subset ablation for Jan-Oct 2025.
Evaluate future models without using final test results for tuning.
```

Most important improvement direction:

```text
Add more representative data, especially data containing high WIP cases and consistently recorded process variables.
```

---

## Final Summary

Validated active artifact:

```text
ml_training/artifacts/wip_final_jan_oct_extra_trees/pipeline.pkl
```

v1 final test performance:

```text
RMSE = 177.37
MAE = 110.00
R2 = 0.102
```

v2 experimental artifact:

```text
ml_training/artifacts/wip_v2_cross_year_extra_trees_log1p/pipeline.pkl
```

v2 final test performance:

```text
RMSE = 196.80
MAE = 124.52
R2 = -0.106
```

Current conclusion:

```text
The v1 Extra Trees model remains the validated artifact for the system. The v2 cross-year model is documented as an experiment because it used more historical data but did not outperform v1 on the final Nov-Dec 2025 test period.
```

Academic conclusion:

```text
The project demonstrates a modular ML-enabled production quality prediction system. The selected model provides better-than-baseline WIP estimation, while the broader system supports data validation, asynchronous inference, reconciliation, and future model artifact replacement through a controlled feature contract.
```
