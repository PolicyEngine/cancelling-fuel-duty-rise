# Cancelling the planned fuel duty rise

A PolicyEngine UK analysis of the cost, counterfactual and distributional impact of cancelling the Autumn Budget 2025 5p fuel-duty reversal. Built around the headlines breaking on **18 May 2026** — Rachel Reeves expected to shelve the planned reversal as part of a cost-of-living package on Thursday 21 May 2026.

The package runs the PolicyEngine UK microsimulation once and writes a media-ready briefing in four formats: interactive **HTML**, **Word DOCX**, multi-sheet **XLSX**, and **standalone PNG / CSV** files for each chart and table.

## What the analysis answers

| Question | Where it lives in the briefing |
|---|---|
| How much does scrapping the planned 5p increase cost the Treasury? | Annual cost chart 2026-27 → 2029-30 |
| What would the duty rate be today if it had risen with RPI every year since the first freeze (Budget 2011)? | Rate-path chart 2011 → 2029 |
| How much money have sixteen years of freezes lost the Treasury? | OBR-style 2010-11 → 2029-30 revenue chart with gap arrow |
| Does PolicyEngine UK reconcile with the £2.4 bn / yr figure quoted by the Guardian (Stacey, 18 May 2026) and the ~£120 bn cumulative figure quoted by Fleet News (Roberts, 18 May 2026)? | Cross-check table |
| Who gains, in £ and as a share of household net income, if the 5p cut is kept? | Distributional charts by quartile, quintile, and decile (bottom 5% excluded) |

## Key numbers (current run)

| | Value |
|---|---|
| Cost of cancelling the planned 5p reversal, 2027-28 (full Autumn Budget plan: 5p + RPI uprating) | **£2.77 bn** |
| Cost of extending the 5p cut alone, 2027-28 (Guardian framing: 52.95p vs 57.95p, no RPI) | **£2.20 bn** — matches the Guardian's £2.4 bn / yr |
| Cumulative cost of freezes 2010-11 → 2026-27 (RPI counterfactual) | **£123 bn** — matches Fleet News ~£120 bn |
| Rate today (2026) if uprated by RPI since 2011 | **100.4 p/L** vs actual 53.4 p/L |
| Annual revenue gap by 2029-30 vs the RPI counterfactual | **£21 bn** |
| Bottom-decile share-of-income gain from keeping the cut (D1, bottom 5% excluded) | **0.50% of net income** vs **0.09%** for the top decile |

(Run `python run.py` for a refreshed copy.)

## Install

```bash
make install         # python -m pip install -e ".[dev]"
```

Set a Hugging Face token to download the enhanced FRS 2023-29 dataset on first run:

```bash
export HUGGING_FACE_TOKEN=hf_…
```

## Run

```bash
python run.py        # writes everything to ./results/
```

That single command runs the PolicyEngine UK simulation once and writes:

| File | Contents |
|---|---|
| `results/analysis.html` | Interactive Plotly briefing, ready to share or host |
| `results/analysis.docx` | Word document with PNG-rendered charts and tables |
| `results/analysis.xlsx` | Ten-sheet workbook covering every dataset used in the briefing |
| `results/chart_annual_cost.png` | Bar chart — cost of cancelling the planned 5p reversal, 2026-27 onwards |
| `results/chart_rate_path.png` | Line chart — actual rate vs RPI counterfactual rate, 2011-2029 |
| `results/chart_obr_style.png` | OBR-style revenue chart with gap arrow, 2010-11 → 2029-30 |
| `results/chart_quartiles.png` | Distributional impact by income quartile |
| `results/chart_quintiles.png` | Distributional impact by income quintile |
| `results/chart_deciles.png` | Distributional impact by income decile (bottom 5% excluded) |
| `results/table_*.csv` | Standalone CSVs of every table used in the briefing |

Each artefact stamps the version of the `policyengine` package that produced it (e.g. *"PolicyEngine (4.3.1); model uk-2.88.0 pinned to policyengine-uk 2.88.0; dataset enhanced_frs_2023_29.h5; OBR RPI series from OBR EFO March 2026"*).

Per-format entry points are also available if you only need one output:

```bash
make html            # python -m cancelling_fuel_duty_rise.build_html
make docx            # python -m cancelling_fuel_duty_rise.build_docx
make xlsx            # python -m cancelling_fuel_duty_rise.build_xlsx
```

All of them share the same in-process `compute_all()` result, so running them sequentially does not re-run the simulation.

## Layout

```
run.py                          one-shot driver — writes everything to ./results/

cancelling_fuel_duty_rise/      installable package
  __init__.py
  theme.py                      PolicyEngine brand palette + Plotly template
  volumes.py                    HMRC out-turn receipts series + named policy anchors
  data.py                       compute_all() — runs PE-UK via policyengine.py
                                and returns the Results dataclass
  charts.py                     Plotly figure builders
  build_html.py                 HTML report assembler (CLI: python -m ...build_html)
  build_docx.py                 DOCX report assembler (CLI: python -m ...build_docx)
  build_xlsx.py                 XLSX workbook assembler (CLI: python -m ...build_xlsx)

notebooks/
  analysis.ipynb                interactive walkthrough that mirrors the briefing

results/                        generated artefacts (gitignored except .gitkeep)
  analysis.html / .docx / .xlsx
  chart_*.png
  table_*.csv

tests/
  test_smoke.py                 import + theme + volumes + policyengine-version checks
```

## Method

### Model and dataset

- The simulation entry point is the unified [`policyengine`](https://github.com/PolicyEngine/policyengine.py) Python package via `policyengine.tax_benefit_models.uk.managed_microsimulation`. That returns a `policyengine_uk.Microsimulation` bound to a specific `policyengine-uk` release (currently 2.88.0) and dataset checksum, with the bundle stamped onto each output's *Sources* line.
- The pinned `policyengine` version is read at runtime from `policyengine.__version__` and cited in every artefact.
- The microdata is the [PolicyEngine UK Data team's enhanced FRS 2023-29 multi-year file](https://huggingface.co/policyengine/policyengine-uk-data) — seven years of household tables (2023-24 → 2029-30) calibrated to OBR aggregates by the PolicyEngine UK data pipeline.

### Reforms compared

| Scenario | Fuel-duty rate path |
|---|---|
| **Baseline (current law)** | Autumn Budget 2025 plan: 52.95p through August 2026, +1p in September 2026, +2p in December 2026, +2p in March 2027, then annual RPI uprating from April 2027 onwards. |
| **Keep the 5p cut** | 52.95p held constant from 2026 onwards — the question the section *"How much does scrapping the 5p increase cost?"* answers (vs the Autumn Budget plan). |
| **5p portion alone** (Guardian framing) | 52.95p vs 57.95p, no RPI uprating after. The cross-check used in the section *"Does this match the Guardian and Fleet News?"*. |
| **RPI counterfactual since 2011** | 57.95p in Budget 2011, compounded by the OBR RPI series every year since. Used for the long-run revenue chart and the 100.4p / litre headline. |

### Parameters and historical data

- The fuel-duty rate history, RPI growth series, and pump-price parameters all come from PolicyEngine UK. Nothing about specific rates or RPI growth is hard-coded in this repo. The 5p-cut date is even *detected* from the parameter values (largest year-on-year rate decrease) rather than written as a date.
- The only fixed numerical inputs in the code are HMRC's published fuel-duty receipts for 2010-11 → 2024-25 (in `cancelling_fuel_duty_rise/volumes.py`, sourced from [HMRC's UK Tax & NICs receipts publication on gov.uk](https://www.gov.uk/government/statistics/hmrc-tax-and-nics-receipts-for-the-uk)) and the documented policy-event years `FIRST_FREEZE_YEAR = 2011` and `FIVE_PENCE_CUT_YEAR = 2022`.

### Weighting

All weighted aggregates use the native `microdf` `MicroSeries` API — `.sum()`, `.mean()`, and `.groupby(...).mean()`. Weights are baked into PolicyEngine UK's `.calculate(...)` return values, so the package never multiplies values by weights by hand.

### Distributional cuts

- Households are ranked on the PolicyEngine UK `equiv_hbai_household_net_income` variable, with household weights multiplied by household size to give person-weighting (the standard HBAI convention).
- Following the [Resolution Foundation's energy-price analysis](https://resolutionfoundation.substack.com/p/higher-energy-prices-could-leave), the bottom 5% by equivalised income is excluded from the distributional cuts (households with very low reported income often have implausibly high consumption in the FRS sample). The remaining 95% is split into quartiles, quintiles, and deciles.

### Caveats

- **No behavioural response.** Fuel volumes are held fixed across scenarios — changing the rate changes revenue but not litres bought. See [PolicyEngine UK data issue #402](https://github.com/PolicyEngine/policyengine-uk-data/issues/402) for the related question of how PE-UK currently projects fuel consumption (uprated by CPI, which is a separate methodological issue being addressed upstream).
- **Population microsimulation, not behavioural model.** Distributional results are accounting impacts on each household at fixed pre-reform behaviour.
- **PE-UK aggregates can drift from OBR.** PolicyEngine UK calibrates household weights to the OBR's `fuel_duties` target each release; the per-decile distribution can move slightly between calibration releases.

## Cross-checks

| Source (18 May 2026) | Quoted | PolicyEngine UK | Match |
|---|---|---|---|
| [Guardian (Kiran Stacey)](https://www.theguardian.com/politics/2026/may/18/rachel-reeves-fuel-duty-cost-of-living) | £2.4 bn / yr for extending the 5p cut | £2.14 bn (2026-27) · £2.20 bn (2027-28) | ✅ |
| Fleet News (Gareth Roberts) | ~£120 bn cumulative cost of freezes 2010/11 → 2026/27 | £123 bn | ✅ |

The two press numbers use the "extend the 5p cut" framing (52.95p vs a return to 57.95p, no further RPI uprating). The headline £2.77 bn (2027-28) in the briefing is bigger because it compares against the full Autumn Budget 2025 plan — i.e. it also captures the April-2027 RPI uprating that Reeves' move would cancel.

## Tests

```bash
make test            # python -m pytest tests/ -v
```

Smoke tests cover imports, the Plotly theme, the HMRC receipts series, and that the `policyengine` version is resolvable at runtime.

## Reproducibility

```bash
python run.py
```

is deterministic for a fixed combination of `policyengine`, `policyengine-uk` and dataset versions. Every artefact carries the citation string showing exactly which versions were used.
