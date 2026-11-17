# Vactosertib trial RNA pathway analysis

[The dated package](2026-11-17/README.md) includes the final reviewed all28 aggregate results and portable sources. The [consolidated report](https://youngcrc.com/reports/research/immunotherapy_resistance_report_2026-11-17_trial_analysis.pdf) contains 64 pages and is pinned in the release record. This package accompanies website release 1.74; its scoped candidate catalogue preserves the separate FOG-001 addition from website release 1.73.

All 28 available baseline trial RNA samples were quantified with the fixed reference and kit-specific preprocessing. None of four prespecified TGF-beta/fibroblast/ECM mean-rank scores showed a significant association with study-defined clinical benefit after BH4 correction (all q=0.521). Clinical benefit means confirmed CR/PR or stable disease maintained at least six months: five versus 23. The two-versus-26 objective-response comparison has a separate exploratory BH4 family. No prespecified sensitivity has a nominal P<0.05.

The analysis does not validate high archival pathway expression as a vactosertib-selection biomarker and does not rule out benefit. Archival sampling, unknown biopsy organ, clinical confounding, library-quality differences and small event counts limit interpretation. No untreated comparator, treatment-effect interaction or personal response estimate is available. Therapeutic priorities are not upgraded from these results.

```sh
python3 analysis/vactosertib-pathways/2026-11-17/scripts/verify_package.py --require-results
python3 analysis/vactosertib-pathways/2026-11-17/scripts/verify_package.py --require-final
python3 -m pip install -r analysis/vactosertib-pathways/2026-11-17/requirements.txt
python3 analysis/vactosertib-pathways/2026-11-17/tests/test_statistics_synthetic.py
python3 analysis/vactosertib-pathways/2026-11-17/analysis/independent_verify_final_statistics.py --self-test
```

The final gate additionally verifies the report; it blocks until the distinct report sources and PDF metadata are approved. Synthetic checks do not access real trial expression or reproduce statistics without external inputs. Read the [release record](../../release/vactosertib_pathways_2026-11-17.json) and package reproduction boundaries. The root clinical/site snapshot remains historical1.53; the Monash-corrected1.72 case package and all previous additions are preserved.
