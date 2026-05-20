"""Smoke tests: avoid running the full microsimulation."""

import importlib
import json
from unittest.mock import patch


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


def test_dataset_download_is_release_pinned():
    from cancelling_fuel_duty_rise.simulation import (
        DEFAULT_ANALYSIS_YEARS,
        DEFAULT_DATASET_METHOD_NOTE,
        DEFAULT_DATASET_NAME,
        DEFAULT_DATASET_REPO_TYPE,
        DEFAULT_DATASET_REVISION,
    )

    assert DEFAULT_DATASET_NAME == "enhanced_frs_2023_24"
    assert DEFAULT_ANALYSIS_YEARS == list(range(2023, 2030))
    assert DEFAULT_DATASET_REPO_TYPE == "model"
    assert DEFAULT_DATASET_REVISION == "1.55.5"
    assert DEFAULT_DATASET_REVISION not in {"main", "latest"}
    assert "policyengine-uk-data#404" in DEFAULT_DATASET_METHOD_NOTE


def test_policyengine_uk_bundle_is_certified_release():
    from importlib.metadata import version

    from policyengine.tax_benefit_models.uk import uk_latest

    assert version("policyengine-uk") == "2.88.14"
    assert uk_latest.data_certification.certified_for_model_version == "2.88.14"
