# Cancelling the planned fuel duty rise

PolicyEngine UK analysis of the cost, counterfactual, and distributional impact of cancelling the Autumn Budget 2025 fuel-duty plan. The package runs one PolicyEngine microsimulation and writes a media-ready briefing as HTML, DOCX, XLSX, PNG charts, and CSV tables. An interactive Next.js dashboard surfaces the same results.

## Dashboard

The interactive analysis dashboard is deployed at <https://cancelling-fuel-duty-rise.vercel.app>. Source lives in [`dashboard/`](./dashboard); pushes to `main` redeploy automatically via Vercel.

To run it locally:

```bash
make sync-dashboard          # regenerate dashboard/public/data/fuel_duty_results.json
cd dashboard && npm install && npm run dev
```

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

This uses `uv sync --locked --extra dev`, so the analysis runs against the reviewed `policyengine.py` release in `uv.lock`. Set a Hugging Face token to download the enhanced FRS dataset on first run:

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
  build_json.py                 JSON exporter that feeds the dashboard

dashboard/                      Next.js (App Router) interactive analysis app
  app/                          page.jsx, layout.jsx, globals.css
  src/components/               Analysis / Methodology / Media tabs
  src/lib/                      data helpers, formatters, chart utilities
  public/data/                  fuel_duty_results.json synced from the pipeline

tests/
  test_smoke.py                 import, benchmark, dependency, and method checks
```

## Method

- **Simulation entry point**: the unified [`policyengine`](https://github.com/PolicyEngine/policyengine.py) Python package via `policyengine.tax_benefit_models.uk.managed_microsimulation`.
- **Runtime UK model and dataset**: resolved by the installed `policyengine.py` managed UK bundle. The project pins `policyengine[uk]==4.9.2` rather than pinning `policyengine-uk` or `policyengine-core` separately.
- **Fiscal totals**: HMRC road-fuel clearances and UK Tax & NICs receipts out-turns, plus OBR March 2026 fuel-duty receipts forecasts. Rate-difference costs use OBR/HMRC all-road petrol + diesel litres as the control total.
- **Distributional allocation**: PolicyEngine provides calibrated household petrol and diesel litres; household savings are those litres times the relevant duty-rate gap. Weighted operations use native `microdf` methods.
- **Dataset**: the `enhanced_frs_2023_24` dataset selected by the active `policyengine.py` UK bundle, projected through the 2023-2029 analysis years by PolicyEngine.
- **Behaviour**: no behavioural response is modelled; fuel volumes are held fixed across scenarios.

### ITV methodology note

policyengine.py provides the household microsimulation and calibrated fuel-litre distribution. Headline fiscal totals use HMRC/OBR fiscal-year road-fuel clearances and receipts, while distributional savings apply the same duty-rate gap to PolicyEngine's calibrated household litres.

## Tests

```bash
make test
```

CI runs smoke tests and the build workflow. Full report generation requires a `HUGGING_FACE_TOKEN` repository secret with read access to `policyengine/policyengine-uk-data-private`.
