"""Read-only audit of the public vactosertib Source Data workbook.

No raw-read processing, outcome modelling, hypothesis tests or patient tissue use.
Run with bundled Python/openpyxl. De-duplicate treatment-history rows by subject;
join IHC source tables to independently recorded RECIST/clinical-benefit labels.
"""
from pathlib import Path
import collections
import csv
import hashlib
import json
import statistics
import openpyxl

ROOT=Path(__file__).resolve().parents[1]
import argparse,tempfile,urllib.request
parser=argparse.ArgumentParser();parser.add_argument('--source',type=Path);parser.add_argument('--fetch',action='store_true');parser.add_argument('--output-dir',type=Path,default=ROOT/'recomputed/literature');args=parser.parse_args()
OUT=args.output_dir;OUT.mkdir(parents=True,exist_ok=True)
SOURCE_URL='https://static-content.springer.com/esm/art%3A10.1038%2Fs41467-026-75595-4/MediaObjects/41467_2026_75595_MOESM6_ESM.xlsx'
EXPECTED_SHA256='8f5fe5ec50d58c43cd420e329e9ea9c63246be38e0f38fea55130815b8c0cf53'
_workspace=tempfile.TemporaryDirectory(prefix='vactosertib-audit-')
if args.source:SOURCE=args.source
elif args.fetch:
    SOURCE=Path(_workspace.name)/'source.xlsx';urllib.request.urlretrieve(SOURCE_URL,SOURCE)
else:parser.error('Use --source for the originalpublicworkbook, or --fetch to downloadit temporarily.')
assert hashlib.sha256(SOURCE.read_bytes()).hexdigest()==EXPECTED_SHA256,'Originalworkbook hash mismatch; no data accepted.'
w = openpyxl.load_workbook(SOURCE, read_only=True, data_only=True)
rows = list(w["Suppl Dataset2"].iter_rows(values_only=True))
header = list(rows[1])
subjects = {}
conflicts = []
for row in rows[2:]:
    if not isinstance(row[0], (int, float)):
        continue
    sid = str(int(row[0]))
    record = dict(zip(header, row))
    if sid in subjects:
        for key in header[:14] + header[17:]:
            if subjects[sid][key] != record[key]:
                conflicts.append([sid, key, subjects[sid][key], record[key]])
    else:
        subjects[sid] = record

audit = {
    "source_file": SOURCE_URL,
    "source_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
    "clinical_subject_count": len(subjects),
    "static_duplicate_conflicts": conflicts,
    "objective_responders": sum(x["RESPONDER"] == "Yes" for x in subjects.values()),
    "clinical_benefit": sum(x["CLINICAL BENEFIT"] == "Yes" for x in subjects.values()),
    "definitions": {
        "objective_responder": "Confirmed RECIST complete or partial response; all 13 were partial responses.",
        "clinical_benefit": "Confirmed CR/PR or stable disease lasting at least six months; 16 total, including three durable-SD cases.",
        "prohibition": "Do not use SD of any duration, clinical benefit, objective response and pharmacodynamic response interchangeably."
    },
    "ihc": {},
    "rna_processed_matrix": {
        "sheet": "Suppl Fig5",
        "columns": list(list(w["Suppl Fig5"].iter_rows(values_only=True))[1]),
        "type": "Dose-group post-treatment versus baseline DESeq2 summary; baseMean pools samples, is not patient baseline TPM and has no individual response labels.",
        "row_count_excluding_title_and_header": w["Suppl Fig5"].max_row - 2,
        "baseline_response_similarity_computable": False
    }
}
joined = []
changes = {}
for sheet in ["Fig5A", "Fig5B", "Fig5C"]:
    data = list(w[sheet].iter_rows(values_only=True))
    cols = list(data[1])
    local = []
    for row in data[2:]:
        if not isinstance(row[0], (int, float)):
            continue
        sid = str(int(row[0]))
        rec = {"subject": sid, **{k: v for k, v in zip(cols[1:], row[1:]) if k}}
        rec["objective_response"] = subjects[sid]["RESPONDER"]
        rec["clinical_benefit"] = subjects[sid]["CLINICAL BENEFIT"]
        local.append(rec)
        joined.append({"sheet": sheet, **rec})
    summary = {}
    for key in cols[1:]:
        if not key:
            continue
        for group in ["Yes", "No"]:
            vals = [x[key] for x in local if x["clinical_benefit"] == group and isinstance(x[key], (int, float))]
            summary[f"{key}__clinical_benefit_{group}"] = {
                "n": len(vals), "median": statistics.median(vals) if vals else None
            }
    audit["ihc"][sheet] = {
        "n": len(local),
        "objective_responders": sum(x["objective_response"] == "Yes" for x in local),
        "clinical_benefit": sum(x["clinical_benefit"] == "Yes" for x in local),
        "headers": cols, "summary": summary
    }
    if sheet in ["Fig5A", "Fig5B"]:
        changes[sheet] = {}
        for index, name in [(1, "total_CD8_Treg"), (3, "GZMBpos_CD8_Treg")]:
            changes[sheet][name] = {}
            for group in ["Yes", "No"]:
                valid = [r for r in data[2:] if isinstance(r[0], (int, float))
                         and subjects[str(int(r[0]))]["CLINICAL BENEFIT"] == group
                         and isinstance(r[index], (int, float)) and isinstance(r[index + 1], (int, float))]
                changes[sheet][name][group] = {
                    "n": len(valid), "increased": sum(r[index + 1] > r[index] for r in valid),
                    "equal": sum(r[index + 1] == r[index] for r in valid),
                    "decreased": sum(r[index + 1] < r[index] for r in valid)
                }
serum = list(w["Suppl Fig4"].iter_rows(values_only=True))
changes["circulating_day5_change_n"] = dict(collections.Counter(
    r[2] for r in serum[2:] if isinstance(r[0], (int, float))))

assert len(subjects) == 103 and not conflicts
assert audit["objective_responders"] == 13 and audit["clinical_benefit"] == 16
assert audit["ihc"]["Fig5A"]["objective_responders"] == 0
assert audit["ihc"]["Fig5B"]["objective_responders"] == 0
audit["publication_transform"]="Only aggregate counts/medians retained; no subject identifiers, arrays or workbook redistributed."
for name, data in [
    ("vactosertib_source_data_audit.json", audit),
    ("vactosertib_pd_vs_benefit_counts.json", changes),
]:
    (OUT / name).write_text(json.dumps(data, indent=2) + "\n")

with (OUT / "vactosertib_baseline_ihc_summary.csv").open("w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["source_sheet", "measure", "clinical_benefit", "n", "median", "interpretation_limit"])
    for sheet in ["Fig5A", "Fig5B"]:
        for key, value in audit["ihc"][sheet]["summary"].items():
            if "_Pre" in key:
                measure, group = key.split("__clinical_benefit_")
                writer.writerow([sheet, measure, group, value["n"], value["median"],
                                 "Only two durable-SD benefit cases and zero objective responders; no validated cutoff, no case spatial-IHC counterpart."])
print(json.dumps({"subjects": len(subjects), "objective_responders": audit["objective_responders"],
                  "IHC_objective_responders": 0, "IHC_benefit_cases": 2}))
