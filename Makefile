VENV = .venv
REQUIREMENTS = requirements.txt
PYTHON = /usr/bin/env python3

.PHONY: install test clean run get

$(VENV):
	$(PYTHON) -m venv $(VENV)
	$(VENV)/bin/pip install --upgrade pip

install: requirements.txt | $(VENV)
	$(VENV)/bin/pip install -r $(REQUIREMENTS)

run: install
	$(VENV)/bin/python ./split_excel.py
	$(VENV)/bin/python ./mod_excel.py
	$(VENV)/bin/python ./create_summary.py
	$(VENV)/bin/python ./create_config.py
	$(VENV)/bin/python ./ss_uploader.py set
	$(VENV)/bin/python ./ss_uploader.py update

run_engine: install
	$(VENV)/bin/python ./split_excel.py
	$(VENV)/bin/python ./mod_excel.py
	$(VENV)/bin/python ./create_summary_engine.py
	$(VENV)/bin/python ./create_config.py
	$(VENV)/bin/python ./ss_uploader.py set
	$(VENV)/bin/python ./ss_uploader.py update

run_reports: install
	$(VENV)/bin/python ./split_excel.py
	$(VENV)/bin/python ./mod_excel.py
	$(VENV)/bin/python ./create_config.py
	$(VENV)/bin/python ./ss_uploader.py set
	$(VENV)/bin/python ./ss_uploader.py update

run_simple: install
	$(VENV)/bin/python ./ss_uploader.py set
	$(VENV)/bin/python ./ss_uploader.py update

setup: install
	$(VENV)/bin/python ./split_excel.py
	$(VENV)/bin/python ./mod_excel.py
	$(VENV)/bin/python ./create_summary_engine.py
	$(VENV)/bin/python ./create_config.py

dupes: install
	$(VENV)/bin/python ./duplicate_parts.py

config: install
	$(VENV)/bin/python ./create_config.py

update: install
	$(VENV)/bin/python ./ss_uploader.py update

summary: install
	$(VENV)/bin/python ./create_summary.py

get: install
	$(VENV)/bin/python ./ss_uploader.py get

test: install
	$(VENV)/bin/python ./ss_uploader.py update -c ./data/config.toml

clean:
	rm -rf $(VENV)
	rm -f Effectivity_Reports_Mod/*
	rm -f Effectivity_Reports_Split/*
