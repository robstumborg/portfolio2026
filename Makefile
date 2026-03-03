VENV := .venv
PYTHON := $(VENV)/bin/python
PIP := $(VENV)/bin/pip

.PHONY: build clean setup

build: $(VENV)
	$(PYTHON) build.py

setup: $(VENV)

$(VENV): requirements.txt
	python3 -m venv $(VENV)
	$(PIP) install -r requirements.txt
	touch $(VENV)

clean:
	rm -rf $(VENV) dist/
