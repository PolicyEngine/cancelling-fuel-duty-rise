# Cancelling the planned fuel duty rise

PolicyEngine UK analysis of the cost, counterfactual and distributional impact of cancelling the Autumn Budget 2025 5p fuel-duty reversal.

The package builds a media-ready briefing in three formats from a single shared simulation pass:

- **HTML** — interactive Plotly charts, embedded for sharing
- **DOCX** — Word document with PNG-rendered charts and tables
- **XLSX** — multi-sheet workbook with every underlying dataset

## Install

```bash
make install
```

(or `pip install -e ".[dev]"` directly.)

Set a Hugging Face token to download the enhanced FRS dataset:

```bash
export HUGGING_FACE_TOKEN=hf_…
```

## Build

```bash
make all          # html + docx + xlsx → outputs/
make html
make docx
make xlsx
```

Each format runs PolicyEngine UK once via `cancelling_fuel_duty_rise.data.compute_all` (cached per process) and renders from the same `Results` bundle.

## Layout

```
cancelling_fuel_duty_rise/
  __init__.py
  theme.py          # PolicyEngine palette + Plotly template
  volumes.py        # HMRC out-turn fuel-duty receipts (2010-2024)
  data.py           # compute_all() — runs PE-UK, returns Results dataclass
  charts.py         # Plotly figure builders (annual cost, rate path, OBR-style, distributional)
  build_html.py     # HTML report assembler
  build_docx.py     # DOCX report assembler
  build_xlsx.py     # XLSX workbook assembler

notebooks/
  analysis.ipynb    # interactive walkthrough (mirrors the briefing)

outputs/
  analysis.html
  analysis.docx
  analysis.xlsx

tests/
  test_smoke.py
```

## Cross-checks

The package's figures reconcile with two press numbers published on 18 May 2026:

- [Guardian (Kiran Stacey)](https://www.theguardian.com/politics/2026/may/18/rachel-reeves-fuel-duty-cost-of-living) — "£2.4 bn / year" cost of extending the 5p cut
- Fleet News (Gareth Roberts) — "~£120 bn cumulative cost of freezes 2010/11 → 2026/27"

See the "Does this match the Guardian and Fleet News?" section of the report for the framing difference between the published figures and the headline `£2.77 bn (2027-28)` cost of cancelling the *full* Autumn Budget 2025 plan (5p reversal + April-2027 RPI uprating).

## Method

- **Microsimulation**: the unified [PolicyEngine Python package](https://github.com/PolicyEngine/policyengine.py) (`policyengine`), which pins a `policyengine-uk` release and dataset bundle for reproducibility. The package version is read at runtime via `policyengine.__version__` and printed in the report sources line.
- **Dataset**: enhanced Family Resources Survey 2023-29 multi-year build, downloaded from the PolicyEngine UK Hugging Face repo.
- **Rate parameters and RPI series**: pulled from `policyengine-uk` (`gov.hmrc.fuel_duty.petrol_and_diesel`, `gov.economic_assumptions.yoy_growth.obr.rpi` — OBR EFO March 2026).
- **Pre-2022 revenue**: HMRC UK Tax & NICs receipts publication on gov.uk.
- **No behavioural responses modelled**: fuel volumes held fixed across scenarios.
- **Distributional cuts**: equivalised HBAI household net income, person-weighted; bottom 5% excluded (Resolution Foundation approach) before splitting the remaining 95% into quartiles / quintiles / deciles.
