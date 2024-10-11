VENV_DIR = .venv
REQUIREMENTS = requirements.txt
PYTHON = /usr/bin/env python

.PHONY: install test clean

venv:
	$(PYTHON) -m venv $(VENV_DIR)
	$(VENV_DIR)/bin/pip install --upgrade pip

install: venv
	$(VENV_DIR)/bin/pip install -r $(REQUIREMENTS)

run: install
	$(VENV_DIR)/bin/python ./ss_api.py set

test: install
	$(VENV_DIR)/bin/python -m unittest discover tests

clean:
	rm -rf $(VENV_DIR)
