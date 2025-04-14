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

hold:
	$(VENV)/bin/python ./ss_uploader.py get -c ./data/A320_config_test.toml
	$(VENV)/bin/python ./reformat_sheets.py
	$(VENV)/bin/python ./create_reformat_config.py A320_config_test.toml
	$(VENV)/bin/python ./ss_uploader.py reformat -c ./data/reformat_config.toml

reformat: install
	$(VENV)/bin/python ./ss_uploader.py get -c ./data/A321_config.toml
	$(VENV)/bin/python ./reformat_sheets.py
	$(VENV)/bin/python ./create_reformat_config.py A321_config.toml
	$(VENV)/bin/python ./ss_uploader.py reformat -c ./data/reformat_config.toml


test: 
	$(VENV)/bin/python ./ss_uploader.py reformat -c ./data/reformat_config.toml

verify:
	$(VENV)/bin/python ./count_rows.py

clean:
	rm -rf $(VENV)

