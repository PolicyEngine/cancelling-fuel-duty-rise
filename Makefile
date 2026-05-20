.PHONY: install run html docx xlsx all clean test format

PYTHON ?= python

install:
	$(PYTHON) -m pip install -e ".[dev]"

run:
	$(PYTHON) run.py

html:
	$(PYTHON) -m cancelling_fuel_duty_rise.build_html

docx:
	$(PYTHON) -m cancelling_fuel_duty_rise.build_docx

xlsx:
	$(PYTHON) -m cancelling_fuel_duty_rise.build_xlsx

all: run

test:
	$(PYTHON) -m pytest tests/ -v

format:
	$(PYTHON) -m ruff format .

clean:
	rm -rf results/*.html results/*.docx results/*.xlsx results/*.png results/*.csv
	find . -type d -name __pycache__ -exec rm -rf {} +
