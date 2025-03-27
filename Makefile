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

feedback: install
	$(VENV)/bin/python ./ss_uploader.py feedback -c ./data/A320_config.toml

feedback_engine: install
	$(VENV)/bin/python ./ss_uploader.py feedback_engine -c ./data/config.toml	

dedupe: install
	$(VENV)/bin/python ./ss_uploader.py dedupe -c ./data/config.toml

dedupe_engine: install
	$(VENV)/bin/python ./ss_uploader.py dedupe_engine -c ./data/config.toml

split: install
	$(VENV)/bin/python ./split_excel.py

test: install
	$(VENV)/bin/python ./ss_uploader.py feedback -c ./data/config.toml

clean:
	rm -rf $(VENV)
	rm -f Effectivity_Reports_Mod/*
	rm -f Effectivity_Reports_Split/*
