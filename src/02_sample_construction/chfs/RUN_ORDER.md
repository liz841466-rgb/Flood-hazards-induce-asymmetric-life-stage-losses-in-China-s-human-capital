# CHFS/CFHS workflow run order

This folder archives the existing Jupyter workflow used to construct household-level
education investment and financial mechanism variables.

The scripts preserve notebook code cells. They are organized according to the original
workflow rather than refactored into a new production pipeline.

## Main workflow

1. `01_wave2011_household_variables.py`
   - Source notebook: `2011/2011.ipynb`
   - Purpose: 2011 household education and finance variables

2. `02_wave2013_household_variables.py`
   - Source notebook: `2013/2013.ipynb`
   - Purpose: 2013 household education and finance variables

3. `03_wave2015_household_variables.py`
   - Source notebook: `2015/2015.ipynb`
   - Purpose: 2015 household education and finance variables

4. `04_wave2017_household_variables.py`
   - Source notebook: `2017/2017.ipynb`
   - Purpose: 2017 household education and finance variables

5. `05_wave2019_household_variables.py`
   - Source notebook: `2019/2019.ipynb`
   - Purpose: 2019 household education and finance variables

6. `06_five_wave_exploratory_analysis.py`
   - Source notebook: internal original notebook (non-public source filename omitted).
   - Purpose: Five-wave exploratory analysis

7. `07_build_unbalanced_household_panel.py`
   - Source notebook: internal original notebook (non-public source filename omitted).
   - Purpose: Build unbalanced household panel

## Notes

- Jupyter checkpoint notebooks are ignored.
- Raw CHFS/CFHS data are not included.
- Processed household-level outputs should not be committed to GitHub.
- Before public release, local absolute paths inside the exported notebook code can be
  replaced by `config.yaml` or command-line arguments if a fully reusable pipeline is needed.
