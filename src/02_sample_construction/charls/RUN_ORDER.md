# Suggested CHARLS code review order

This is the review order matching the original notebook workflow.

## A. Wave-specific construction

For each wave 2011, 2013, 2015, 2018, and 2020:

```text
1. Health status variables
2. Health recoding
3. Age and region variables
4. Composite health index construction
5. Health index, age, and region merge
6. Medical expenditure variables
7. Healthcare access time variables
8. Sex and education controls (2011 optional)
```

In the GitHub archive, these correspond to:

```text
01_wave_health_status.py
02_wave_health_recode.py
03_wave_age_region.py
04_wave_health_index.py
05_wave_health_index_age_region_merge.py
06_wave_medical_expenditure.py
07_wave_healthcare_access_time.py
08_wave_demographic_controls_optional.py
```

## B. Five-wave panel construction

After wave-specific outputs are produced locally, review:

```text
09_joint_unbalanced_panel.py
```

This corresponds to the original five-wave unbalanced panel notebooks.
