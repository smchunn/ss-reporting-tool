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
	$(VENV)/bin/python ./create_config.py
	$(VENV)/bin/python ./ss_uploader.py set

get: install
	$(VENV)/bin/python ./ss_uploader.py get

test: install
	$(VENV)/bin/python ./ss_uploader.py test

clean:
	rm -rf $(VENV)
