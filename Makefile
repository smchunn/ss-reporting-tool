VENV = .venv
REQUIREMENTS = requirements.txt
PYTHON = /usr/bin/env python

.PHONY: install test clean

$(VENV):
	$(PYTHON) -m venv $(VENV)
	$(VENV)/bin/pip install --upgrade pip

install: requirements.txt | $(VENV)
	$(VENV)/bin/pip install -r $(REQUIREMENTS)

run: install
	$(VENV)/bin/python ./ss_uploader.py set

test: install
	$(VENV)/bin/python ./ss_uploader.py test

clean:
	rm -rf $(VENV)
