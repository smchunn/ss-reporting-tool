VENV = .venv
REQUIREMENTS = requirements.txt
PYTHON = /usr/bin/env python3

.PHONY: install test clean run get

$(VENV):
	$(PYTHON) -m venv $(VENV)
	$(VENV)/bin/pip install --upgrade pip

install: requirements.txt | $(VENV)
	$(VENV)/bin/pip install -r $(REQUIREMENTS)

run:
	$(VENV)/bin/python ./ss_uploader.py set -c ./data/config.toml
	$(VENV)/bin/python ./ss_uploader.py update -c ./data/config.toml
	$(VENV)/bin/python ./ss_uploader.py dedupe -c ./data/config.toml
	
get: 
	$(VENV)/bin/python ./ss_uploader.py get -c ./data/A320_config.toml

set:
	$(VENV)/bin/python ./ss_uploader.py set -c ./data/config.toml

feedback: install
	$(VENV)/bin/python ./ss_uploader.py feedback -c ./data/A320_config.toml

feedback_engine: install
	$(VENV)/bin/python ./ss_uploader.py feedback_engine -c ./data/A320_engine_config.toml

split: install
	$(VENV)/bin/python ./split_excel.py
	$(VENV)/bin/python ./reformat_sheets.py

reformat: install
	$(VENV)/bin/python ./ss_uploader.py get -c ./data/A321_config.toml
	$(VENV)/bin/python ./reformat_sheets.py
	$(VENV)/bin/python ./create_reformat_config.py A321_config.toml
	$(VENV)/bin/python ./ss_uploader.py reformat -c ./data/reformat_config.toml

update:
	$(VENV)/bin/python ./ss_uploader.py update -c ./data/A320_config_category.toml

dedupe:
	$(VENV)/bin/python ./ss_uploader.py dedupe -c ./data/A319_config_category.toml

test: 
	$(VENV)/bin/python ./order_excel.py

verify:
	$(VENV)/bin/python ./count_rows.py

lock:
	$(VENV)/bin/python ./ss_uploader.py lock -c ./data/All_config_category.toml

summary: install
	$(VENV)/bin/python ./ss_uploader.py get -c ./data/All_config_category.toml
	$(VENV)/bin/python ./create_summary.py
	$(VENV)/bin/python ./create_summary_category.py
	$(VENV)/bin/python ./ss_uploader.py refresh_summary -c ./data/summary_config.toml

category:
	$(VENV)/bin/python ./create_summary_category.py

refresh:
	$(VENV)/bin/python ./ss_uploader.py refresh_summary -c ./data/summary_config.toml

config:
	$(VENV)/bin/python ./create_config.py

clean:
	rm -rf $(VENV)

