VENV = .venv
REQUIREMENTS = requirements.txt
PYTHON = /usr/bin/env python3
PATH_TO_MODULE = ssh+https://github.com/..../Users/spencer.chunn/Development/python/ss-reporting-tool/
PATH_TO_CONFIG = ./data/test_config.toml

.PHONY: test clean run get set feedback

$(VENV):
	$(PYTHON) -m venv $(VENV)
	$(VENV)/bin/pip install --upgrade pip

install: requirements.txt | $(VENV)
	$(VENV)/bin/pip install -r $(REQUIREMENTS)

dev: $(VENV)
	$(VENV)/bin/pip install -e .

get:
	$(VENV)/bin/python -m ss_reporting_tool get -c $(PATH_TO_CONFIG)

set:
	$(VENV)/bin/python -m ss_reporting_tool set -c $(PATH_TO_CONFIG)

refresh:
	$(VENV)/bin/python -m ss_reporting_tool refresh_summary -c $(PATH_TO_CONFIG) --debug

feedback: install
	$(VENV)/bin/python -m ss_reporting_tool feedback -c $(PATH_TO_CONFIG)

# summary:
# 	$(VENV)/bin/python -m $(MODULE) get -c /Users/silas.bash/Library/CloudStorage/OneDrive-MMC/SmartSheet_API/config_DEMO/A320_A321_config.toml
# 	$(VENV)/bin/python ./src/ss_reporting_tool/create_summary.py
# 	$(VENV)/bin/python ./src/ss_reporting_tool/create_summary_category.py
# 	$(VENV)/bin/python -m $(MODULE) refresh_summary -c /Users/silas.bash/Library/CloudStorage/OneDrive-MMC/SmartSheet_API/config_DEMO/summary_config.toml
test:
	$(VENV)/bin/python -m pytest tests

clean:
	rm -rf $(VENV)

