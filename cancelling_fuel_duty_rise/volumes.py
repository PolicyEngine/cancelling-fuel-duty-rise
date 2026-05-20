"""Historical anchors used by the briefing.

- :data:`FIRST_FREEZE_YEAR` and :data:`FIVE_PENCE_CUT_YEAR` are documented
  policy events held here as named constants so callers don't repeat magic
  numbers. The actual fuel-duty rate values for those events are read from
  the PolicyEngine UK parameter tree, never from this file.
- :data:`HMRC_RECEIPTS_MILLION` is HMRC's published out-turn for fuel-duty
  receipts. PolicyEngine UK microdata only starts in 2022, so the chart
  spanning 2010-11 onwards needs this series to anchor the historical
  segment. See :data:`HMRC_RECEIPTS_SOURCE_URL`.
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
