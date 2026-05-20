"""UK fuel-duty out-turn / projection by fiscal year.

Used to build the 2010-11 -> 2029-30 revenue chart. PolicyEngine UK only
ships microdata from 2022 onwards, so for pre-2022 years we use HMRC's
published Tax & NICs receipts; from 2025 onwards we use the PolicyEngine UK
microsim baseline at the Autumn Budget 2025 schedule.
"""

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
