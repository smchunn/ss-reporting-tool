VENV = .venv
REQUIREMENTS = requirements.txt
PYTHON = /usr/bin/env python3

.PHONY: test clean run get set feedback

$(VENV):
	$(PYTHON) -m venv $(VENV)
	$(VENV)/bin/pip install --upgrade pip

install: requirements.txt | $(VENV)
	$(VENV)/bin/pip install -r $(REQUIREMENTS)

get:
	$(VENV)/bin/python -m $(MODULE) get -c ./data/config.toml

set:
	$(VENV)/bin/python -m $(MODULE) set -c ./data/config.toml

feedback: install
	$(VENV)/bin/python ./ss_uploader.py feedback -c ./data/A320_config.toml

test:
	$(VENV)/bin/python -m pytest tests

clean:
	rm -rf $(VENV)

