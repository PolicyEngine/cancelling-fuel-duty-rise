"""Smoke tests — don't run the full microsim, just import-check + theme."""

import importlib


def test_imports():
    for module in [
        "cancelling_fuel_duty_rise",
        "cancelling_fuel_duty_rise.theme",
        "cancelling_fuel_duty_rise.volumes",
        "cancelling_fuel_duty_rise.charts",
        "cancelling_fuel_duty_rise.data",
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


def test_hmrc_volumes_present():
    from cancelling_fuel_duty_rise.volumes import HMRC_RECEIPTS_MILLION, hmrc_receipts_bn

    assert 2010 in HMRC_RECEIPTS_MILLION
    assert 2024 in HMRC_RECEIPTS_MILLION
    bn = hmrc_receipts_bn()
    assert abs(bn[2024] - 24.165) < 1e-3
