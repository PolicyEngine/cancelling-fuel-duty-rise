"""Smoke tests: avoid running the full microsimulation."""

import importlib
import json
import tomllib
from pathlib import Path
from unittest.mock import patch

from microdf import MicroSeries


def test_imports():
    for module in [
        "cancelling_fuel_duty_rise",
        "cancelling_fuel_duty_rise.theme",
        "cancelling_fuel_duty_rise.historical",
        "cancelling_fuel_duty_rise.charts",
        "cancelling_fuel_duty_rise.simulation",
        "cancelling_fuel_duty_rise.build_html",
        "cancelling_fuel_duty_rise.build_docx",
        "cancelling_fuel_duty_rise.build_xlsx",
    ]:
        importlib.import_module(module)


def test_theme_registers():
    from cancelling_fuel_duty_rise.theme import register_template
    import plotly.io as pio

    register_template()
    assert pio.templates.default == "policyengine"


def test_hmrc_road_fuel_benchmarks_present():
    from cancelling_fuel_duty_rise.historical import (
        FISCAL_YEAR_AVERAGE_DUTY_RATE,
        HMRC_RECEIPTS_MILLION,
        benchmark_cost_bn,
        hmrc_receipts_bn,
        road_fuel_clearances_mlitres,
    )

    assert 2010 in HMRC_RECEIPTS_MILLION
    assert 2024 in HMRC_RECEIPTS_MILLION
    receipts_bn = hmrc_receipts_bn()
    assert abs(receipts_bn[2024] - 24.165) < 1e-3
    assert road_fuel_clearances_mlitres()[2027] > 40_000
    assert round(benchmark_cost_bn(2027, 0.05), 2) == 2.18
    assert (
        round(benchmark_cost_bn(2027, FISCAL_YEAR_AVERAGE_DUTY_RATE[2027] - 0.5295), 2)
        == 3.12
    )


def test_policyengine_version_resolvable():
    """``policyengine`` is the unified entry-point we cite in the report."""
    from cancelling_fuel_duty_rise.simulation import _policyengine_version

    version = _policyengine_version()
    assert isinstance(version, str)
    assert version != ""
    assert version != "unknown"


def test_policyengine_py_owns_uk_runtime_dependency():
    """The analysis should follow one reviewed policyengine.py UK bundle."""
    pyproject = tomllib.loads(Path("pyproject.toml").read_text())
    deps = pyproject["project"]["dependencies"]
    assert "policyengine[uk]==4.11.0" in deps
    assert not any(dep.startswith("policyengine-uk") for dep in deps)
    assert not any(dep.startswith("policyengine-core") for dep in deps)


def test_policyengine_py_uk_stack_imports_without_private_manifest():
    from huggingface_hub import hf_hub_download

    class FakeManifestResponse:
        status_code = 200
        content = json.dumps(
            {
                "schema_version": 1,
                "data_package": {
                    "name": "policyengine-uk-data",
                    "version": "1.55.5",
                },
                "compatible_model_packages": [
                    {
                        "name": "policyengine-uk",
                        "specifier": ">=0",
                    },
                ],
                "default_datasets": {},
                "artifacts": {},
            }
        ).encode("utf-8")
        text = content.decode("utf-8")

        def json(self):
            return json.loads(self.text)

        def raise_for_status(self):
            return None

    with patch("requests.get", return_value=FakeManifestResponse()):
        from policyengine.tax_benefit_models.uk import (
            managed_microsimulation,
            uk_latest,
        )

    assert getattr(uk_latest, "id", "")
    assert callable(managed_microsimulation)
    assert callable(hf_hub_download)


def test_dataset_selection_uses_policyengine_bundle():
    from cancelling_fuel_duty_rise.simulation import (
        DEFAULT_ANALYSIS_YEARS,
        DEFAULT_DATASET_NAME,
        ITV_METHOD_NOTE,
    )

    assert DEFAULT_DATASET_NAME == "enhanced_frs_2023_24"
    assert DEFAULT_ANALYSIS_YEARS == list(range(2023, 2030))
    assert "calibrated petrol and diesel litre distribution" in ITV_METHOD_NOTE
    assert "without post-hoc scaling" in ITV_METHOD_NOTE


def test_distributional_cuts_include_bottom_five_percent():
    from cancelling_fuel_duty_rise.simulation import _distributional_cuts

    class FakeSimulation:
        def calculate(self, variable, year, map_to=None):
            values = list(range(1, 101))
            if variable == "petrol_litres":
                return MicroSeries(values, weights=[1] * 100)
            if variable == "diesel_litres":
                return MicroSeries([0] * 100, weights=[1] * 100)
            if variable in (
                "household_net_income",
                "equiv_hbai_household_net_income",
            ):
                return MicroSeries(values, weights=[1] * 100)
            raise ValueError(variable)

    _, _, deciles = _distributional_cuts(
        baseline_sim=FakeSimulation(),
        year_dist=2027,
        duty_rate_gap=1,
    )

    assert deciles.loc[0, "group"] == "D1"
    assert deciles.loc[0, "avg_net_income_gbp"] == 5.5
    assert deciles.loc[0, "avg_saving_gbp_per_year"] == 5.5


def test_policyengine_uk_bundle_is_certified_by_policyengine_py():
    from importlib.metadata import version

    from policyengine.tax_benefit_models.uk import uk_latest

    pe_version = version("policyengine")
    pe_uk_version = version("policyengine-uk")
    assert uk_latest.release_bundle["policyengine_version"] == pe_version
    assert uk_latest.release_bundle["model_version"] == pe_uk_version
    assert uk_latest.data_certification.certified_for_model_version == pe_uk_version
