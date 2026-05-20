# Cancelling the planned fuel duty rise

PolicyEngine UK analysis of the cost, counterfactual, and distributional impact of cancelling the Autumn Budget 2025 fuel-duty plan. The package runs one PolicyEngine microsimulation and writes a media-ready briefing as HTML, DOCX, XLSX, PNG charts, and CSV tables.

## Key numbers

| Question | Current estimate |
|---|---:|
| Cost of cancelling the full 2027-28 Autumn Budget plan | **£3.12bn** |
| Cost of extending the 5p cut alone in 2027-28, Guardian framing | **£2.18bn** |
| Cost of cancelling the full 2029-30 plan | **£4.42bn** |

The full-plan estimate is larger than the Guardian-style 5p figure because it also includes the April 2027 RPI uprating that would be cancelled.

## Install

```bash
make install
```

This uses `uv sync --extra dev --locked`, so the environment follows the committed lockfile. Set a Hugging Face token to download the enhanced FRS dataset on first run:

```bash
export HUGGING_FACE_TOKEN=hf_...
```

## Run

```bash
uv run python run.py
```

The command writes:

| File | Contents |
|---|---|
| `results/analysis.html` | Interactive Plotly briefing |
| `results/analysis.docx` | Word document with PNG-rendered charts and tables |
| `results/analysis.xlsx` | Multi-sheet workbook covering every dataset used |
| `results/chart_*.png` | Standalone chart images |
| `results/table_*.csv` | Standalone source tables |

## Layout

```text
run.py                          one-shot driver

cancelling_fuel_duty_rise/
  historical.py                 HMRC/OBR receipts, rates, and road-fuel litre benchmarks
  simulation.py                 compute_all(); runs PolicyEngine via policyengine.py
  charts.py                     Plotly figure builders
  build_html.py                 HTML report assembler
  build_docx.py                 DOCX report assembler
  build_xlsx.py                 XLSX workbook assembler

tests/
  test_smoke.py                 import, benchmark, dependency, and method checks
```

## Method

- **Simulation entry point**: the unified [`policyengine`](https://github.com/PolicyEngine/policyengine.py) Python package via `policyengine.tax_benefit_models.uk.managed_microsimulation`.
- **Runtime UK model**: `policyengine-uk` is pinned in `pyproject.toml` / `uv.lock` to the certified `policyengine.py` bundle. The PE-UK fuel-volume-uprating PR should replace this pin after release.
- **Fiscal totals**: HMRC road-fuel clearances and UK Tax & NICs receipts out-turns, plus OBR March 2026 fuel-duty receipts forecasts. Rate-difference costs use OBR/HMRC all-road petrol + diesel litres as the control total.
- **Distributional allocation**: PolicyEngine calculates household impacts; the aggregate is scaled to the fiscal control total. Weighted operations use native `microdf` methods.
- **Dataset**: certified `policyengine.py` UK bundle dataset `enhanced_frs_2023_24` from `policyengine/policyengine-uk-data-private` at revision `1.55.5` by default, projected through the 2023-2029 analysis years by PolicyEngine. This released build predates the UK-data litre-proxy training PR, so the fiscal headline totals use the HMRC/OBR road-fuel controls directly; the distributional allocation will pick up the new LCFS fuel-spending training method after PolicyEngine/policyengine-uk-data#404 is released and rebuilt. Set `POLICYENGINE_UK_DATA_REVISION` to override it.
- **Behaviour**: no behavioural response is modelled; fuel volumes are held fixed across scenarios.

## Tests

```bash
make test
```

CI runs smoke tests and the build workflow. Full report generation requires a `HUGGING_FACE_TOKEN` repository secret with read access to `policyengine/policyengine-uk-data-private`.
