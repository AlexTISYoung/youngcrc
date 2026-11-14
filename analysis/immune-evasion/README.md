# Immune-evasion analyses

## 14 November 2026 revision

- [Analysis instructions and limits](2026-11-14/README.txt)
- [Eight-axis and within-axis therapeutic rankings](2026-11-14/rankings.json)
- [Sources, input hashes and transformations](2026-11-14/source_manifest.json)
- [Package checksums](2026-11-14/package_manifest.json)
- [Report source and citations](2026-11-14/report/)
- [Reviewed PDF](https://youngcrc.com/reports/research/immune_evasion_report_2026-11-14.pdf)
- [Release record and PDF checksum](../../release/immune_evasion_2026-11-14.json)

The revision re-examines 337 RNA targets and 279 protein targets, incorporates the new assay-matched Caris biopsy percentiles, and ranks eight immune-evasion axes and therapeutics within each axis. The report retains counterevidence, access limits and discriminating experiments. These are research priorities, not response probabilities or treatment recommendations. Archival tissue does not establish the dominant mechanism in the recent node.

From the repository root:

```sh
python3 analysis/immune-evasion/2026-11-14/verify_package.py --rerun
```

The default table rerun is offline and uses Python's standard library. An optional, hash-pinned full protein database supports independent peptide-specificity checks. Report generation additionally needs `python-docx`; rendering and visual review are separate steps. No new clinical variant calling or mass-spectrum search is performed.

This focused addition accompanies website release 1.68. It does not synchronize the repository's historical 1.53 clinical tables or website source with the live website. Consult the current website manifest for current availability; cite this package's date, repository commit and file hashes. The reviewed PDF is hosted separately, not embedded in Git.
