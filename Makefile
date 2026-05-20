.PHONY: install run html docx xlsx all clean test format

UV ?= uv

install:
	$(UV) sync --locked --extra dev

run:
	$(UV) run python run.py

html:
	$(UV) run python -m cancelling_fuel_duty_rise.build_html

docx:
	$(UV) run python -m cancelling_fuel_duty_rise.build_docx

xlsx:
	$(UV) run python -m cancelling_fuel_duty_rise.build_xlsx

all: run

test:
	$(UV) run pytest tests/ -v

format:
	$(UV) run ruff format .

clean:
	rm -rf results/*.html results/*.docx results/*.xlsx results/*.png results/*.csv
	find . -type d -name __pycache__ -exec rm -rf {} +
