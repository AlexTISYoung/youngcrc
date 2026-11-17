from pathlib import Path
import argparse,json,shutil,subprocess,sys
SOURCE=Path(__file__).resolve().parent
p=argparse.ArgumentParser();p.add_argument('--output-dir',type=Path,required=True);args=p.parse_args()
dest=args.output_dir.resolve();m=dest/'data/molecular';m.mkdir(parents=True,exist_ok=True)
shutil.copy2(SOURCE/'inputs/baseline_summary.json',m/'summary.json')
shutil.copy2(SOURCE/'inputs/variant_crosswalk.json',m/'variants.json')
plan=json.loads((SOURCE/'update_script_provenance.json').read_text())
for name in plan['execution_order']:
 subprocess.run([sys.executable,str(SOURCE/'scripts'/name),str(dest)],check=True)
expected=json.loads((SOURCE/'summary.json').read_text())
actual=json.loads((m/'summary.json').read_text())
assert actual==expected,'Molecular summary differs from reviewed snapshot'
print('Reproduced reviewed molecular summary exactly (semantic JSON comparison).')
