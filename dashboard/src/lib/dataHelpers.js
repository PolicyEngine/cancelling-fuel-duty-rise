/**
 * Data helper functions for the fuel-duty dashboard.
 *
 * The dashboard consumes a single JSON file produced by
 * cancelling_fuel_duty_rise.build_json. Callers must guard the loading state
 * above; these helpers assume `data` is already loaded and surface real errors
 * if a required key is missing.
 */

export function fyLabel(year) {
  return `${year}-${String((year + 1) % 100).padStart(2, "0")}`;
}

export function getHeadline(data) {
  return data.headline;
}

export function getCitation(data) {
  return data.citation;
}

export function getMethodNote(data) {
  return data.method_note;
}

export function getScrap5pCost(data) {
  return data.tables.scrap_5p_cost.map((row) => ({
    year: row.Year,
    fy: fyLabel(row.Year),
    baselineRate: row["Baseline rate (p/L)"],
    baselineRevenueBn: row["Baseline revenue (£bn)"],
    reformRevenueBn: row["Reform revenue (£bn)"],
    costBn: row["Cost to Treasury (£bn)"],
  }));
}

export function getGuardianCheck(data) {
  return data.tables.guardian_check.map((row) => ({
    year: row.Year,
    fy: fyLabel(row.Year),
    revenueAt5295pBn: row["Revenue at 52.95p (£bn)"],
    revenueAt5795pBn: row["Revenue at 57.95p (£bn)"],
    cost5pBn: row["Cost of keeping 5p cut (£bn)"],
  }));
}

export function getRatePath(data) {
  return data.tables.rate_path.map((row) => ({
    year: row.year,
    fy: fyLabel(row.year),
    rpiYoyPct: row.rpi_yoy_growth_pct,
    actualP: row.actual_rate_p_per_litre,
    counterfactualP: row.rpi_counterfactual_rate_p_per_litre,
    gapP: row.gap_p_per_litre,
  }));
}

export function getRateHistory(data) {
  return (data.tables.rate_history ?? []).map((row) => ({
    date: row.date,
    rateP: row.rate_pence_per_litre,
  }));
}

export function getLitreCheck(data) {
  return (data.tables.litre_check ?? []).map((row) => ({
    year: row.Year,
    fy: fyLabel(row.Year),
    peLitresBn: row["PolicyEngine litres (bn)"],
    benchmarkLitresBn: row["HMRC/OBR litres (bn)"],
    ratio: row["PolicyEngine / HMRC-OBR"],
    rateGapP: row["Duty-rate gap (p/L)"],
    peCostBn: row["PolicyEngine cost (£bn)"],
    benchmarkCostBn: row["HMRC/OBR cost (£bn)"],
  }));
}

export function getRevenueSeries(data) {
  return data.tables.revenue_2010_2029.map((row) => ({
    year: row.year,
    fy: row.fiscal_year,
    source: row.source,
    actualP: row.actual_rate_p_per_litre,
    counterfactualP: row.counterfactual_rate_p_per_litre,
    actualBn: row.actual_revenue_gbp_bn,
    counterfactualBn: row.counterfactual_revenue_gbp_bn,
    gapBn: row.gap_gbp_bn,
  }));
}

const GROUP_KEY = {
  deciles: { count: 10, prefix: "D", label: "decile" },
  quintiles: { count: 5, prefix: "Q", label: "quintile" },
  quartiles: { count: 4, prefix: "Q", label: "quartile" },
};

function mapDistributionRow(row, meta) {
  return {
    group: row.group,
    avgSaving: row.avg_saving_gbp_per_year,
    avgNetIncome: row.avg_net_income_gbp,
    savingPctOfIncome: row.saving_pct_of_net_income,
    pctWinners: row.pct_winners ?? null,
    pctUnchanged: row.pct_unchanged ?? null,
    meta,
  };
}

export function getDistribution(data, grouping, year) {
  const meta = GROUP_KEY[grouping];
  const byYearKey = `${grouping}_by_year`;
  const byYear = data.distribution[byYearKey];
  // Per-year data preferred when available + a year is specified.
  if (year != null && byYear && byYear[String(year)]) {
    return byYear[String(year)].map((row) => mapDistributionRow(row, meta));
  }
  const rows = data.distribution[grouping];
  if (!rows) {
    throw new Error(`No distribution data for grouping=${grouping}`);
  }
  return rows.map((row) => mapDistributionRow(row, meta));
}

export function getDistributionYears(data) {
  return data.distribution.years ?? [data.headline.year_dist];
}

export function getDistributionDefaultYear(data) {
  return data.distribution.default_year ?? data.headline.year_dist;
}

export function getGroupingMeta(grouping) {
  return GROUP_KEY[grouping];
}
