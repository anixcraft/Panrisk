# Model Card: Pancreatic Cancer Risk Screening (research prototype)

## Intended use
Educational and research demonstration of an explainable, calibrated, multilingual risk-screening workflow.
**Not a medical device. Not for diagnosis or clinical decisions.**

## Data
Debernardi et al. (2020), urinary biomarkers for pancreatic cancer (CC-BY). 590 samples; the target here is
PDAC (199) vs. control + benign hepatobiliary disease (391). Single study, several hospitals, no external validation.

## Model
Random Forest (300 trees, depth 6, balanced class weights) in a scikit-learn Pipeline, isotonic-calibrated (5-fold).
Inputs: age, sex, creatinine, LYVE1, REG1B, TFF1, plasma CA19-9 (optional), REG1A (optional) + "was measured" flags.
Deliberately excluded: `stage`, `benign_sample_diagnosis` (label leakage); `sample_origin`, `patient_cohort`
(study-design variables a real user cannot supply).

## Performance (held-out test set n=118; trained on n=472)
| Metric | Value |
|---|---|
| ROC-AUC | 0.9779 |
| Brier score | 0.0505 |
| Decision threshold (chosen on out-of-fold training predictions, target sensitivity >= 0.90) | 0.24 |
| Sensitivity | 0.95 |
| Specificity | 0.8718 |
| Precision | 0.7917 |
| Confusion matrix [[TN, FP], [FN, TP]] | [[68, 10], [2, 38]] |

At this screening-oriented threshold, 10 of 48 flagged test cases were false alarms.

## Subgroup sensitivity at the deployed threshold
| Group | n | Positives | Sensitivity |
|---|---|---|---|
| sex=F | 67 | 21 | 0.905 |
| sex=M | 51 | 19 | 1.000 |
| age <50 | 29 | 1 | 1.000 |
| age 50-65 | 48 | 13 | 0.923 |
| age >65 | 41 | 26 | 0.962 |

Subgroups are tiny (e.g. only 1 positive under age 50), so these numbers can neither show fairness nor unfairness;
they only flag where to look once more data is available.

## Explainability
SHAP (TreeExplainer) on the underlying forest. Top global drivers by mean |SHAP|: plasma_CA19_9, LYVE1, TFF1, REG1B, age, creatinine.
Per-patient explanations appear as plain-language sentences. SHAP explains the forest's ranking, not the calibrated probability exactly.

## Risk bands (design choice, not clinically validated)
High: p >= threshold. Inconclusive: 0.6 x threshold <= p < threshold. Low: below that. Displayed score is clipped to 1-99%.

## Known limitations
- Small, single-study dataset; no external validation; performance on new populations is unknown.
- CA19-9 and REG1A were measured only in subsets of patients by study design; missingness is encoded as a flag.
- Controls and benign cases come from specific hospitals; site effects may still leak through biology-looking features.
- Hindi/Marathi text is drafted and needs native-speaker (and clinical-communication) review.
- Inputs outside the training range trigger a warning; the model extrapolates poorly.

## Ethics
Research use only. The app stores no user data. Any real deployment would need clinical validation, regulatory review and professional oversight.
