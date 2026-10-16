.PHONY: check verify summary
check: verify
	python3 -m unittest discover -s tests -p 'test_*.py' -v
	python3 examples/summarize_case.py > /dev/null
verify:
	python3 scripts/case_data.py verify-snapshot --json
summary:
	python3 examples/summarize_case.py
