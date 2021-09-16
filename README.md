# Project CKD
> classifying progression of a patient's CKD staging


**Problem Statement**

For this task, you are given a set of longitudinal data (attached) of different lab measurements for patients diagnosed with chronic kidney disease (CKD). Furthermore, you are also given the information whether these patients progress in their CKD stage or not in the future. Using this dataset, you are required to come up with a solution to predict whether a patient will progress in CKD staging given the patient's past longitudinal information.

The following CSV files are provided:

1. T_demo.csv
> `id`:patient id, `race`: patient’s race, `gender`: patient’s gender, `age`: patient’s age at baseline

2. T_creatinine.csv
> `id`:patient id, `value`: patient’s serum creatinine value at the corresponding time (in mg/dl), `time`: time of measurement (in days from baseline t=0)

3. T_DBP.csv
> `id`:patient id, `value`: patient’s diastolic blood pressure at the corresponding time (in mmHg), `time`: time of measurement (in days from baseline t=0)
4. T_SBP.csv
> `id`:patient id, `value`: patient’s systolic blood pressure at the corresponding time (in mmHg), `time`: time of measurement (in days from baseline t=0)
5. T_HGB.csv
> `id`:patient id, `value`: patient’s Hemoglobin level at the corresponding time (in g/dl), `time`: time of measurement (in days from baseline t=0)
6. T_glucose.csv
> `id`:patient id, `value`: patient’s glucose level at the corresponding time (in mmol/l), `time`: time of measurement (in days from baseline t=0)

7. T_ldl.csv
> `id`:patient id, `value`: patient’s low-density lipoprotein (LDL-c) level at the corresponding time (in mg/dl), `time`: time of measurement (in days from baseline t=0)
8. T_meds.csv
> `id`:patient id, `drug`: the name of the drug being prescribed `daily_dosage`: the dosage of the drug being prescribed (in mg) `start_day`: the starting time of the prescription (in days from baseline t=0) `end_day`: the end of the prescription (in days from baseline t=0)
9. T_stage.csv
> `id`:patient id, `Stage_Progress`: indicator of whether or not the patient progress in the CKD stage (True=progress)

**Sequence of Notebooks**

00_EDA and Setting Baseline
> Attempts to understand the data and the task

01_Tabular Model.
> Uses to TabularModel to solve the given task

02_SAINT TabularModel
> Uses the SAINT architecture/framework to solve the given task

03_Conclusion
> Conclusion and future recommendations

04_Graph NN
> Attempts to define the problem as a graph problem
