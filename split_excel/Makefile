VENV = .venv
REQUIREMENTS = requirements.txt
PYTHON = /usr/bin/env python3
EXECUTABLE = dist/split_excel

.PHONY: install build run clean

$(VENV):
	$(PYTHON) -m venv $(VENV)
	$(VENV)/bin/pip install --upgrade pip

install: requirements.txt | $(VENV)
	$(VENV)/bin/pip install -r $(REQUIREMENTS)

build: install
	$(VENV)/bin/pyinstaller --onefile split_excel.py

run: build
	./$(EXECUTABLE)

clean:
	rm -rf $(VENV)
	rm -rf build
	rm -rf dist
	rm -rf split_excel.spec
