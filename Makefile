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
	$(VENV)/bin/python ./create_config.py
	$(VENV)/bin/python ./mod_excel.py
	$(VENV)/bin/python ./ss_uploader.py set
	$(VENV)/bin/python ./ss_uploader.py update

config: install
	$(VENV)/bin/python ./create_config.py
	
update: install
	$(VENV)/bin/python ./ss_uploader.py update

summary: install
	$(VENV)/bin/python ./ss_uploader.py summary

get: install
	$(VENV)/bin/python ./ss_uploader.py get

test: install
	$(VENV)/bin/python ./ss_uploader.py test

clean:
	rm -rf $(VENV)
	rm -f Effectivity_Reports_Mod/*
	rm -f Effectivity_Reports_Split/*
