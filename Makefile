.PHONY: install html docx xlsx all clean test format

PYTHON ?= python

install:
	$(PYTHON) -m pip install -e ".[dev]"

html:
	$(PYTHON) -m cancelling_fuel_duty_rise.build_html

docx:
	$(PYTHON) -m cancelling_fuel_duty_rise.build_docx

xlsx:
	$(PYTHON) -m cancelling_fuel_duty_rise.build_xlsx

all: html docx xlsx

test:
	$(PYTHON) -m pytest tests/ -v

format:
	$(PYTHON) -m ruff format .

clean:
	rm -rf outputs/*.html outputs/*.docx outputs/*.xlsx
	find . -type d -name __pycache__ -exec rm -rf {} +
