"""Historical anchors used by the briefing.

- :data:`FIRST_FREEZE_YEAR` and :data:`FIVE_PENCE_CUT_YEAR` are documented
  policy events held here as named constants so callers don't repeat magic
  numbers. The actual fuel-duty rate values for those events are read from
  the PolicyEngine UK parameter tree, never from this file.
- :data:`HMRC_RECEIPTS_MILLION` is HMRC's published out-turn for fuel-duty
  receipts. PolicyEngine UK microdata only starts in 2022, so the chart
  spanning 2010-11 onwards needs this series to anchor the historical
  segment. See :data:`HMRC_RECEIPTS_SOURCE_URL`.
- Fuel-duty cost benchmarks use HMRC road-fuel clearances historically and
  OBR March 2026 forecast receipts converted to litres over the forecast.
"""

# Documented policy anchors. Values are deliberately constants — the
# corresponding rates / RPI growth come from the PolicyEngine UK parameter
# tree at runtime.
FIRST_FREEZE_YEAR = 2011
"""Year the fuel-duty escalator was first frozen (Budget 2011)."""

FIVE_PENCE_CUT_YEAR = 2022
"""Year Sunak's temporary 5p cut was introduced."""

OBR_FORECAST_VINTAGE = "OBR EFO March 2026"
"""OBR forecast vintage used by the PolicyEngine UK RPI series at runtime."""

HMRC_RECEIPTS_SOURCE_URL = (
    "https://www.gov.uk/government/statistics/hmrc-tax-and-nics-receipts-for-the-uk"
)

# HMRC fuel-duty receipts, fiscal year, £ million. Source: HMRC UK Tax & NIC
# receipts publication (gov.uk).
HMRC_RECEIPTS_MILLION = {
    2010: 27_283,
    2011: 26_798,
    2012: 26_571,
    2013: 26_881,
    2014: 27_153,
    2015: 27_572,
    2016: 27_898,
    2017: 27_888,
    2018: 28_031,
    2019: 27_620,
    2020: 20_929,
    2021: 25_940,
    2022: 25_068,
    2023: 24_704,
    2024: 24_165,
}


def hmrc_receipts_bn() -> dict[int, float]:
    """HMRC out-turn fuel-duty receipts in £ billion."""
    return {year: value / 1000.0 for year, value in HMRC_RECEIPTS_MILLION.items()}


# Fiscal-year UK petrol + diesel clearances, million litres. Historical out-turn
# is HMRC Hydrocarbon Oils Bulletin Table 2a. Forecasts are OBR March 2026 fuel
# duty receipts, net of non-road receipts, divided by the fiscal-year average
# petrol/diesel duty rate.
HMRC_ROAD_FUEL_CLEARANCES_MLITRES = {
    2020: 35_289.7611569628,
    2021: 43_906.907618977,
    2022: 46_653.9535006421,
    2023: 46_386.741837677,
    2024: 46_327.0970704816,
}

OBR_FUEL_DUTY_RECEIPTS_GBP_BN = {
    2025: 24.241874775213375,
    2026: 24.628571426324807,
    2027: 26.545622366266198,
    2028: 26.63575593480781,
    2029: 26.382076806202907,
    2030: 25.740748126281627,
}

NON_ROAD_FUEL_RECEIPTS_GBP_BN = {
    2025: 0.2,
    2026: 0.3,
    2027: 0.3,
    2028: 0.3,
    2029: 0.3,
    2030: 0.3,
}

FISCAL_YEAR_AVERAGE_DUTY_RATE = {
    2025: 0.5295,
    2026: (0.5295 * 153 + 0.5395 * 91 + 0.5595 * 90 + 0.5795 * 31) / 365,
    2027: 0.6010,
    2028: 0.6198,
    2029: 0.6376,
    2030: 0.6562,
}


def forecast_road_fuel_clearances_mlitres() -> dict[int, float]:
    """OBR-implied road-fuel clearances, in million litres."""
    return {
        year: (
            OBR_FUEL_DUTY_RECEIPTS_GBP_BN[year] - NON_ROAD_FUEL_RECEIPTS_GBP_BN[year]
        )
        * 1_000
        / FISCAL_YEAR_AVERAGE_DUTY_RATE[year]
        for year in OBR_FUEL_DUTY_RECEIPTS_GBP_BN
    }


def road_fuel_clearances_mlitres(end_year: int | None = None) -> dict[int, float]:
    """Road-fuel clearances, carrying the final OBR forecast year forward."""
    series = {
        **HMRC_ROAD_FUEL_CLEARANCES_MLITRES,
        **forecast_road_fuel_clearances_mlitres(),
    }
    if end_year is None:
        return series

    last_year = max(series)
    last_value = series[last_year]
    for year in range(last_year + 1, end_year + 1):
        series[year] = last_value
    return series


def road_fuel_clearances_bn_litres(year: int) -> float:
    """Road-fuel clearances in billion litres for a fiscal year."""
    return road_fuel_clearances_mlitres(end_year=year)[year] / 1_000


def benchmark_cost_bn(year: int, rate_gap_gbp_per_litre: float) -> float:
    """Fiscal cost from OBR/HMRC road-fuel litres and a duty-rate gap."""
    return road_fuel_clearances_bn_litres(year) * rate_gap_gbp_per_litre


def benchmark_receipts_bn(year: int, rate_gbp_per_litre: float) -> float:
    """Fuel-duty receipts benchmark for the current-law fiscal-year chart."""
    if year in HMRC_RECEIPTS_MILLION:
        return HMRC_RECEIPTS_MILLION[year] / 1_000
    if year in OBR_FUEL_DUTY_RECEIPTS_GBP_BN:
        return OBR_FUEL_DUTY_RECEIPTS_GBP_BN[year]
    non_road = NON_ROAD_FUEL_RECEIPTS_GBP_BN[max(NON_ROAD_FUEL_RECEIPTS_GBP_BN)]
    return road_fuel_clearances_bn_litres(year) * rate_gbp_per_litre + non_road
