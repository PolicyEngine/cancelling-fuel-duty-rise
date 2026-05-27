"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Line,
  LineChart,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { colors } from "../lib/colors";
import {
  fyLabel,
  getDistribution,
  getDistributionDefaultYear,
  getDistributionYears,
  getGuardianCheck,
  getHeadline,
  getRatePath,
  getRevenueSeries,
  getScrap5pCost,
} from "../lib/dataHelpers";
import { formatBn, formatCurrency } from "../lib/formatters";
import { getNiceTicks, getTickDomain } from "../lib/chartUtils";
import ChartLogo from "./ChartLogo";
import SectionHeading from "./SectionHeading";

const PALETTE = {
  grid: colors.border.light,
  text: colors.gray[700],
  muted: colors.gray[500],
  gain: colors.primary[700],
  gainSoft: colors.primary[500],
  loss: colors.error,
  counterfactual: colors.gray[500],
};

const AXIS_STYLE = {
  fontSize: 12,
  fill: colors.gray[500],
};

const GROUPING_OPTIONS = [
  { id: "deciles", label: "Deciles", description: "Ten equal slices of the income distribution." },
  { id: "quintiles", label: "Quintiles", description: "Five equal slices of the income distribution." },
  { id: "quartiles", label: "Quartiles", description: "Four equal slices of the income distribution." },
];

function CustomTooltip({ active, payload, label, formatter, labelFormatter }) {
  if (!active || !payload?.length) return null;
  return (
    <div className="rounded-xl border border-slate-200 bg-white px-4 py-3 text-sm shadow-lg">
      {label !== undefined ? (
        <div className="mb-2 font-semibold text-slate-800">
          {labelFormatter ? labelFormatter(label) : label}
        </div>
      ) : null}
      {payload.map((entry) => (
        <div className="flex items-center justify-between gap-4" key={entry.name}>
          <span className="flex items-center gap-2 text-slate-600">
            <span
              className="h-2.5 w-2.5 rounded-full"
              style={{ backgroundColor: entry.color }}
            />
            {entry.name}
          </span>
          <span className="font-medium text-slate-800">
            {formatter ? formatter(entry.value, entry.name) : entry.value}
          </span>
        </div>
      ))}
    </div>
  );
}

function YearDropdown({ value, options, onChange }) {
  const [open, setOpen] = useState(false);
  const containerRef = useRef(null);
  const current = options.find((o) => o.id === value);

  useEffect(() => {
    if (!open) return;
    function handleClick(event) {
      if (containerRef.current && !containerRef.current.contains(event.target)) {
        setOpen(false);
      }
    }
    function handleKey(event) {
      if (event.key === "Escape") setOpen(false);
    }
    document.addEventListener("mousedown", handleClick);
    document.addEventListener("keydown", handleKey);
    return () => {
      document.removeEventListener("mousedown", handleClick);
      document.removeEventListener("keydown", handleKey);
    };
  }, [open]);

  return (
    <div className="relative" ref={containerRef}>
      <button
        type="button"
        aria-haspopup="listbox"
        aria-expanded={open}
        className="flex items-center gap-1.5 rounded-md border border-slate-200 bg-white px-3 py-1.5 text-xs font-medium text-slate-700 hover:border-slate-300 hover:bg-slate-50"
        onClick={() => setOpen((v) => !v)}
      >
        <span className="text-slate-400">Year:</span>
        <span>{current?.label}</span>
        <svg
          width="10"
          height="10"
          viewBox="0 0 10 10"
          aria-hidden="true"
          className={`transition-transform ${open ? "rotate-180" : ""}`}
        >
          <path
            d="M2 4l3 3 3-3"
            fill="none"
            stroke="currentColor"
            strokeWidth="1.5"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        </svg>
      </button>
      {open && (
        <div
          role="listbox"
          className="absolute right-0 z-20 mt-1 w-40 overflow-hidden rounded-lg border border-slate-200 bg-white shadow-lg"
        >
          {options.map((opt) => {
            const active = opt.id === value;
            return (
              <button
                key={opt.id}
                role="option"
                aria-selected={active}
                type="button"
                className={`flex w-full px-3 py-2 text-left text-xs ${
                  active
                    ? "bg-primary-50 font-semibold text-primary-700"
                    : "text-slate-700 hover:bg-slate-50"
                }`}
                onClick={() => {
                  onChange(opt.id);
                  setOpen(false);
                }}
              >
                {opt.label}
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
}

function GroupingDropdown({ value, onChange }) {
  const [open, setOpen] = useState(false);
  const containerRef = useRef(null);
  const current = GROUPING_OPTIONS.find((o) => o.id === value);

  useEffect(() => {
    if (!open) return;
    function handleClick(event) {
      if (containerRef.current && !containerRef.current.contains(event.target)) {
        setOpen(false);
      }
    }
    function handleKey(event) {
      if (event.key === "Escape") setOpen(false);
    }
    document.addEventListener("mousedown", handleClick);
    document.addEventListener("keydown", handleKey);
    return () => {
      document.removeEventListener("mousedown", handleClick);
      document.removeEventListener("keydown", handleKey);
    };
  }, [open]);

  return (
    <div className="relative" ref={containerRef}>
      <button
        type="button"
        aria-haspopup="listbox"
        aria-expanded={open}
        className="flex items-center gap-1.5 rounded-md border border-slate-200 bg-white px-3 py-1.5 text-xs font-medium text-slate-700 hover:border-slate-300 hover:bg-slate-50"
        onClick={() => setOpen((v) => !v)}
      >
        <span className="text-slate-400">Group by:</span>
        <span>{current.label}</span>
        <svg
          width="10"
          height="10"
          viewBox="0 0 10 10"
          aria-hidden="true"
          className={`transition-transform ${open ? "rotate-180" : ""}`}
        >
          <path
            d="M2 4l3 3 3-3"
            fill="none"
            stroke="currentColor"
            strokeWidth="1.5"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        </svg>
      </button>
      {open && (
        <div
          role="listbox"
          className="absolute right-0 z-20 mt-1 w-60 overflow-hidden rounded-lg border border-slate-200 bg-white shadow-lg"
        >
          {GROUPING_OPTIONS.map((opt) => {
            const active = opt.id === value;
            return (
              <button
                key={opt.id}
                role="option"
                aria-selected={active}
                type="button"
                className={`flex w-full flex-col items-start gap-0.5 px-3 py-2 text-left text-xs ${
                  active
                    ? "bg-primary-50 text-primary-700"
                    : "text-slate-700 hover:bg-slate-50"
                }`}
                onClick={() => {
                  onChange(opt.id);
                  setOpen(false);
                }}
              >
                <span className="font-semibold">{opt.label}</span>
                <span className={active ? "text-primary-600/80" : "text-slate-500"}>
                  {opt.description}
                </span>
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
}

export default function ReformTab({ data }) {
  const headline = useMemo(() => getHeadline(data), [data]);
  const ratePath = useMemo(() => getRatePath(data), [data]);
  const scrap5p = useMemo(() => getScrap5pCost(data), [data]);
  const guardian = useMemo(() => getGuardianCheck(data), [data]);
  const revenueSeries = useMemo(() => getRevenueSeries(data), [data]);

  // Trim both annual-cost charts to years where the reform actually
  // differs from current law (2026-27 onwards) — earlier years are
  // either zero or matching the status quo and just clutter the axis.
  const REFORM_START = 2026;
  const scrap5pReform = useMemo(
    () => scrap5p.filter((row) => row.year >= REFORM_START),
    [scrap5p],
  );
  const guardianReform = useMemo(
    () => guardian.filter((row) => row.year >= REFORM_START),
    [guardian],
  );

  const distributionYears = useMemo(() => getDistributionYears(data), [data]);
  const defaultDistYear = useMemo(
    () => getDistributionDefaultYear(data),
    [data],
  );
  const yearDropdownOptions = useMemo(
    () => distributionYears.map((y) => ({ id: y, label: fyLabel(y) })),
    [distributionYears],
  );

  // Saving chart
  const [grouping, setGrouping] = useState("deciles");
  const [impactMode, setImpactMode] = useState("abs");
  const [savingYear, setSavingYear] = useState(defaultDistYear);
  const distribution = useMemo(
    () => getDistribution(data, grouping, savingYear),
    [data, grouping, savingYear],
  );

  // Winners chart — independent state
  const [winnersGrouping, setWinnersGrouping] = useState("deciles");
  const [winnersYear, setWinnersYear] = useState(defaultDistYear);
  const winnersDistribution = useMemo(
    () => getDistribution(data, winnersGrouping, winnersYear),
    [data, winnersGrouping, winnersYear],
  );

  const yearDist = headline.year_dist;
  const lastYear = headline.last_year;
  const firstFreeze = headline.first_freeze_year;

  const guardian2027 = guardian.find((row) => row.year === 2027);

  const distTicks = useMemo(() => {
    if (impactMode !== "abs") return undefined;
    const allValues = distribution.map((row) => row.avgSaving);
    return getNiceTicks([Math.min(0, ...allValues), Math.max(0, ...allValues)]);
  }, [distribution, impactMode]);

  const distDomain = distTicks ? getTickDomain(distTicks) : undefined;

  return (
    <div className="space-y-8">
      <SectionHeading
        title="Who is affected by cancelling the fuel-duty rise?"
        description={
          <>
            The{" "}
            <a
              href="https://www.gov.uk/government/publications/budget-2025-document/budget-2025-html"
              target="_blank"
              rel="noreferrer"
            >
              Autumn Budget 2025
            </a>{" "}
            plan unwinds the 5p-per-litre cut from March 2022 in three steps
            (+1p Sept 2026, +2p Dec 2026, +2p Mar 2027) and resumes RPI
            uprating in April 2027. By the {fyLabel(2027)} fiscal-year average,
            petrol and diesel duty is{" "}
            {headline.baseline_rate_2027_p.toFixed(2)}p/L (up from 52.95p
            today), and reaches{" "}
            {ratePath[ratePath.length - 1].actualP.toFixed(2)}p/L by{" "}
            {fyLabel(lastYear)}. In May 2026 the Prime Minister{" "}
            <a
              href="https://fleetworld.co.uk/fuel-duty-increase-delayed-until-2027-says-starmer/"
              target="_blank"
              rel="noreferrer"
            >
              postponed the September step
            </a>{" "}
            amid Middle-East pump-price pressure, extending the freeze
            through end-of-year; the figures below cost the original Budget
            2025 schedule rather than any slipped version. This page costs the alternative of holding duty flat
            at 52.95p/L: the annual revenue loss, where it lands
            across households in {fyLabel(yearDist)}, and how the long-running
            freeze compares to a counterfactual where duty had been RPI-uprated
            every year since {fyLabel(firstFreeze)}. Fiscal totals use HMRC
            out-turns and OBR projections; household savings apply the same
            duty-rate gap to PolicyEngine's calibrated petrol &amp; diesel
            litres. As a sanity check, our actual-rate receipts series
            (£24.24bn in {fyLabel(2025)}, £26.55bn in {fyLabel(2027)}) sits
            within ~1% of the{" "}
            <a
              href="https://obr.uk/forecasts-in-depth/tax-by-tax-spend-by-spend/fuel-duties/"
              target="_blank"
              rel="noreferrer"
            >
              OBR EFO forecast
            </a>{" "}
            (£24.0bn and £26.2bn).
          </>
        }
      />

      {/* Headline metric cards */}
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <div className="metric-card">
          <div className="text-xs font-medium uppercase tracking-[0.08em] text-slate-500">
            Cost of cancelling the full plan, {fyLabel(2027)}
          </div>
          <div className="mt-2 text-3xl font-bold tracking-tight text-slate-900 tabular-nums">
            {formatBn(headline.scrap_2027)}
          </div>
          <div className="mt-1 text-sm text-slate-500">
            The Treasury loses this much in {fyLabel(2027)} if duty stays at
            52.95p/L instead of rising to{" "}
            {headline.baseline_rate_2027_p.toFixed(2)}p/L as scheduled.
          </div>
        </div>
        <div className="metric-card">
          <div className="text-xs font-medium uppercase tracking-[0.08em] text-slate-500">
            Cost of just extending the 5p cut, {fyLabel(2027)}
          </div>
          <div className="mt-2 text-3xl font-bold tracking-tight text-slate-900 tabular-nums">
            {formatBn(guardian2027.cost5pBn)}
          </div>
          <div className="mt-1 text-sm text-slate-500">
            Narrower framing used in press coverage: 52.95p vs the pre-cut
            57.95p only. Excludes the April 2027 RPI uprating, which is why
            it's smaller than the full-plan figure.
          </div>
        </div>
        <div className="metric-card">
          <div className="text-xs font-medium uppercase tracking-[0.08em] text-slate-500">
            Cumulative receipts foregone since {fyLabel(firstFreeze)}
          </div>
          <div className="mt-2 text-3xl font-bold tracking-tight text-slate-900 tabular-nums">
            {formatBn(headline.fleet_cumulative)}
          </div>
          <div className="mt-1 text-sm text-slate-500">
            How much extra duty would have been collected if the rate had
            risen by RPI every April since {fyLabel(firstFreeze)}, summed
            year-by-year through {fyLabel(2026)}.
          </div>
        </div>
        <div className="metric-card">
          <div className="text-xs font-medium uppercase tracking-[0.08em] text-slate-500">
            5p extension cost, {fyLabel(lastYear)}
          </div>
          <div className="mt-2 text-3xl font-bold tracking-tight text-slate-900 tabular-nums">
            {formatBn(
              data.tables.guardian_check.find((r) => r.Year === lastYear)[
                "Cost of keeping 5p cut (£bn)"
              ],
            )}
          </div>
          <div className="mt-1 text-sm text-slate-500">
            Our {fyLabel(lastYear)} figure for the narrower "extend the 5p
            cut" framing. The{" "}
            <a
              href="https://ifs.org.uk/articles/response-todays-announcement-road-and-fuel-taxation"
              target="_blank"
              rel="noreferrer"
            >
              IFS
            </a>{" "}
            puts the same number at ~£2.3bn/yr by {fyLabel(lastYear)}.
          </div>
        </div>
      </div>

      {/* What is changing — sits as a section, not a boxed card */}
      <div>
        <SectionHeading
          title="What is changing"
          description="The Autumn Budget 2025 plan ends the 5p cut in April 2027 and resumes RPI uprating. The reform we cost holds duty at 52.95p/L."
        />
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-slate-200 text-left text-[11px] uppercase tracking-wide text-slate-400">
                <th className="py-2 pr-4 font-medium">Parameter</th>
                <th className="py-2 pr-4 font-medium">Pre-2022</th>
                <th className="py-2 pr-4 font-medium">Today (frozen)</th>
                <th className="py-2 pr-4 font-medium">{fyLabel(2027)} plan</th>
                <th className="py-2 pr-4 font-medium">{fyLabel(lastYear)} plan</th>
                <th className="py-2 pr-0 font-medium">
                  RPI counterfactual ({fyLabel(lastYear)})
                </th>
              </tr>
            </thead>
            <tbody className="text-slate-700">
              <tr className="border-b border-slate-100 align-top">
                <td className="py-3 pr-4">
                  <div className="font-semibold">Petrol &amp; diesel duty (p/L)</div>
                  <div className="mt-0.5 text-xs text-slate-500">
                    Headline rate set at the UK Budget; CPI/RPI uprating
                    suspended since {fyLabel(firstFreeze)}.
                  </div>
                </td>
                <td className="py-3 pr-4 tabular-nums">57.95p</td>
                <td className="py-3 pr-4 tabular-nums">52.95p</td>
                <td className="py-3 pr-4 tabular-nums">
                  {headline.baseline_rate_2027_p.toFixed(2)}p
                </td>
                <td className="py-3 pr-4 tabular-nums">
                  {ratePath[ratePath.length - 1].actualP.toFixed(2)}p
                </td>
                <td className="py-3 pr-0 tabular-nums">
                  {ratePath[ratePath.length - 1].counterfactualP.toFixed(2)}p
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      {/* Annual cost — full plan vs Guardian 5p framing, side-by-side */}
      <SectionHeading
        title="Annual cost to the Treasury"
        description="Year-by-year cost of cancelling the rise, under two framings: scrapping the full Budget 2025 plan, or just extending the 5p cut. Same year window on both so the bars line up."
      />
      <div className="grid gap-8 xl:grid-cols-2">
        <div className="section-card">
          <SectionHeading
            title="Cost of cancelling the full plan, by year"
            description={`How much revenue the Treasury loses each year if duty is held at 52.95p/L instead of rising as the Budget plans. Shown for ${fyLabel(REFORM_START)}–${fyLabel(lastYear)} only — earlier years already match the reform, so the cost is zero by definition.`}
          />
          <div className="h-[380px] w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={scrap5pReform}>
                <CartesianGrid strokeDasharray="3 3" stroke={PALETTE.grid} />
                <XAxis dataKey="fy" tick={AXIS_STYLE} tickLine={false} />
                <YAxis
                  tick={AXIS_STYLE}
                  tickLine={false}
                  axisLine={false}
                  tickFormatter={(v) => `£${v}bn`}
                />
                <ReferenceLine y={0} stroke={colors.gray[400]} strokeWidth={1} />
                <Tooltip
                  content={<CustomTooltip formatter={(v) => formatBn(v)} />}
                />
                <Bar dataKey="costBn" name="Full plan" fill={PALETTE.gain} radius={[6, 6, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
          <ChartLogo />
        </div>

        <div className="section-card">
          <SectionHeading
            title="Cost of just extending the 5p cut, by year"
            description={`A narrower question: what if the only thing we cancel is the 5p reversal — duty stays at 52.95p/L instead of returning to the pre-cut 57.95p/L? These bars are smaller than the full-plan chart on the left because they don't include the April 2027 RPI uprating, which the Budget also adds on top.`}
          />
          <div className="h-[380px] w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={guardianReform}>
                <CartesianGrid strokeDasharray="3 3" stroke={PALETTE.grid} />
                <XAxis dataKey="fy" tick={AXIS_STYLE} tickLine={false} />
                <YAxis
                  tick={AXIS_STYLE}
                  tickLine={false}
                  axisLine={false}
                  tickFormatter={(v) => `£${v}bn`}
                />
                <ReferenceLine y={0} stroke={colors.gray[400]} strokeWidth={1} />
                <Tooltip
                  content={<CustomTooltip formatter={(v) => formatBn(v)} />}
                />
                <Bar
                  dataKey="cost5pBn"
                  name="5p only"
                  fill={PALETTE.gainSoft}
                  radius={[6, 6, 0, 0]}
                />
              </BarChart>
            </ResponsiveContainer>
          </div>
          <ChartLogo />
        </div>
      </div>

      {/* Rate path + OBR-style revenue — side-by-side */}
      <SectionHeading
        title="Long-run trend"
        description={`Where today's frozen duty rate sits against a counterfactual where it had risen by RPI every April since ${fyLabel(firstFreeze)}, and what that has meant for receipts year-by-year. The left panel shows it in pence-per-litre terms; the right panel translates the same gap into £bn of duty receipts.`}
      />
      <div className="grid gap-8 xl:grid-cols-2">
        <div className="section-card">
        <SectionHeading
          title="Duty rate path — what was vs what it would have been"
          description={`Solid line: the actual duty rate charged each year, including the planned Budget 2025 increases through ${fyLabel(lastYear)}. Dashed line: a counterfactual where duty had simply risen by RPI every April since ${fyLabel(firstFreeze)}. The gap between the two is what's been lost to the de-facto freeze.`}
        />
        <div className="h-[380px] w-full">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={ratePath} margin={{ top: 10, right: 16, left: 4, bottom: 8 }}>
              <CartesianGrid strokeDasharray="3 3" stroke={PALETTE.grid} />
              <XAxis
                dataKey="year"
                tick={AXIS_STYLE}
                tickLine={false}
                type="number"
                domain={["dataMin", "dataMax"]}
                ticks={ratePath.filter((_, i) => i % 2 === 0).map((r) => r.year)}
              />
              <YAxis
                tick={AXIS_STYLE}
                tickLine={false}
                axisLine={false}
                tickFormatter={(v) => `${v}p`}
              />
              <Tooltip
                content={
                  <CustomTooltip
                    formatter={(v) => `${Number(v).toFixed(2)}p/L`}
                    labelFormatter={(v) => `${fyLabel(v)}`}
                  />
                }
              />
              <Legend
                wrapperStyle={{ fontSize: 12, paddingTop: 12 }}
                iconSize={10}
                verticalAlign="bottom"
              />
              <Line
                type="monotone"
                dataKey="actualP"
                stroke={PALETTE.gain}
                strokeWidth={2.5}
                dot={false}
                activeDot={{ r: 5 }}
                name="Actual rate"
              />
              <Line
                type="monotone"
                dataKey="counterfactualP"
                stroke={PALETTE.counterfactual}
                strokeWidth={2.5}
                strokeDasharray="6 4"
                dot={false}
                activeDot={{ r: 5 }}
                name="RPI counterfactual"
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
        <ChartLogo />
      </div>

        {/* OBR-style revenue chart — right column of the side-by-side grid */}
        {revenueSeries.length > 0 && (
        <div className="section-card">
          <SectionHeading
            title="Fuel duty receipts — actual vs RPI counterfactual"
            description={`The same comparison in revenue terms. Solid line: actual UK fuel duty receipts each year (HMRC out-turns through ${fyLabel(2024)}, OBR March 2026 EFO forecast thereafter). Dashed line: what receipts would have been at the RPI-uprated counterfactual rate. The shaded area is the cumulative £${headline.fleet_cumulative.toFixed(0)}bn foregone since ${fyLabel(firstFreeze)}.`}
          />
          <div className="h-[380px] w-full">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart
                data={revenueSeries}
                margin={{ top: 10, right: 16, left: 4, bottom: 8 }}
              >
                <defs>
                  <linearGradient id="gapFill" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor={PALETTE.counterfactual} stopOpacity={0.25} />
                    <stop offset="95%" stopColor={PALETTE.counterfactual} stopOpacity={0.05} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke={PALETTE.grid} />
                <XAxis
                  dataKey="year"
                  tick={AXIS_STYLE}
                  tickLine={false}
                  type="number"
                  domain={["dataMin", "dataMax"]}
                  ticks={revenueSeries
                    .filter((_, i) => i % 2 === 0)
                    .map((r) => r.year)}
                />
                <YAxis
                  tick={AXIS_STYLE}
                  tickLine={false}
                  axisLine={false}
                  tickFormatter={(v) => `£${v}bn`}
                />
                <Tooltip
                  content={
                    <CustomTooltip
                      formatter={(v) => formatBn(v)}
                      labelFormatter={(v) => `${fyLabel(v)}`}
                    />
                  }
                />
                <Legend
                  wrapperStyle={{ fontSize: 12, paddingTop: 12 }}
                  iconSize={10}
                  verticalAlign="bottom"
                />
                <Area
                  type="monotone"
                  dataKey="counterfactualBn"
                  stroke={PALETTE.counterfactual}
                  strokeWidth={2.5}
                  strokeDasharray="6 4"
                  fill="url(#gapFill)"
                  name="RPI counterfactual"
                  activeDot={{ r: 5 }}
                />
                <Area
                  type="monotone"
                  dataKey="actualBn"
                  stroke={PALETTE.gain}
                  strokeWidth={2.5}
                  fill="#ffffff"
                  fillOpacity={0.85}
                  name="Actual receipts"
                  activeDot={{ r: 5 }}
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
          <ChartLogo />
        </div>
        )}
      </div>

      {/* Distribution: saving + winners/losers — side-by-side */}
      <SectionHeading
        title="Household impact"
        description="How the saving from cancellation lands across UK households: the average per-household gain by income group, and the share of households in each group that actually benefit. Use the Year dropdown on each chart to pick a fiscal year — the two charts are independent so you can compare different years side-by-side."
      />
      <div className="grid gap-8 xl:grid-cols-2">
      <div className="section-card">
        <div className="mb-4 flex flex-wrap items-start justify-between gap-3">
          <SectionHeading
            title={`Average household saving by income group (${fyLabel(savingYear)})`}
            description={
              impactMode === "abs"
                ? "How much the average household in each income group keeps per year if the planned rise is cancelled. Calculated as their petrol + diesel litres times the duty-rate gap, averaged across every household in the group (not just car-owning households)."
                : "The same saving expressed as a percentage of the household's net income — useful for seeing which groups benefit most in relative terms."
            }
          />
          <div className="flex flex-shrink-0 items-center gap-2">
            <div className="flex overflow-hidden rounded-md border border-slate-200 bg-white text-xs font-medium">
              <button
                className={`px-3 py-1.5 ${
                  impactMode === "abs"
                    ? "bg-primary-600 text-white"
                    : "text-slate-600 hover:bg-slate-50"
                }`}
                onClick={() => setImpactMode("abs")}
              >
                £
              </button>
              <button
                className={`px-3 py-1.5 ${
                  impactMode === "pct"
                    ? "bg-primary-600 text-white"
                    : "text-slate-600 hover:bg-slate-50"
                }`}
                onClick={() => setImpactMode("pct")}
              >
                %
              </button>
            </div>
            <YearDropdown
              value={savingYear}
              options={yearDropdownOptions}
              onChange={setSavingYear}
            />
            <GroupingDropdown value={grouping} onChange={setGrouping} />
          </div>
        </div>
        <div className="h-[380px] w-full">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={distribution}>
              <CartesianGrid strokeDasharray="3 3" stroke={PALETTE.grid} />
              <XAxis dataKey="group" tick={AXIS_STYLE} tickLine={false} />
              <YAxis
                ticks={distTicks}
                domain={distDomain}
                tick={AXIS_STYLE}
                tickLine={false}
                axisLine={false}
                tickFormatter={
                  impactMode === "abs"
                    ? (v) => formatCurrency(v)
                    : (v) => `${Number(v).toFixed(2)}%`
                }
              />
              <ReferenceLine y={0} stroke={colors.gray[400]} strokeWidth={1} />
              <Tooltip
                content={
                  <CustomTooltip
                    formatter={
                      impactMode === "abs"
                        ? (value) => `${formatCurrency(value)}/yr`
                        : (value) => `${Number(value).toFixed(2)}%`
                    }
                  />
                }
              />
              <Bar
                dataKey={impactMode === "abs" ? "avgSaving" : "savingPctOfIncome"}
                name={
                  impactMode === "abs"
                    ? "Average saving"
                    : "Saving as % of net income"
                }
                radius={[6, 6, 0, 0]}
              >
                {distribution.map((row, i) => (
                  <Cell
                    key={`d-${i}`}
                    fill={
                      (impactMode === "abs"
                        ? row.avgSaving
                        : row.savingPctOfIncome) >= 0
                        ? PALETTE.gain
                        : PALETTE.loss
                    }
                  />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
        <ChartLogo />
      </div>

      {winnersDistribution[0]?.pctWinners != null && (
        <div className="section-card">
          <div className="mb-4 flex flex-wrap items-start justify-between gap-3">
            <SectionHeading
              title={`Winners and unchanged by income group (${fyLabel(winnersYear)})`}
              description={
                <>
                  Share of households in each income group that come out ahead
                  under the reform (gain &gt; £0) versus those whose net
                  position is unchanged because they don't buy petrol or
                  diesel. No-one loses — cancelling a duty rise can only
                  leave a household the same or better off.
                </>
              }
            />
            <div className="flex flex-shrink-0 items-center gap-2">
              <YearDropdown
                value={winnersYear}
                options={yearDropdownOptions}
                onChange={setWinnersYear}
              />
              <GroupingDropdown
                value={winnersGrouping}
                onChange={setWinnersGrouping}
              />
            </div>
          </div>
          <div className="h-[380px] w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart
                data={winnersDistribution}
                margin={{ top: 10, right: 12, left: 4, bottom: 8 }}
              >
                <CartesianGrid strokeDasharray="3 3" stroke={PALETTE.grid} />
                <XAxis dataKey="group" tick={AXIS_STYLE} tickLine={false} />
                <YAxis
                  tick={AXIS_STYLE}
                  tickLine={false}
                  axisLine={false}
                  ticks={[0, 25, 50, 75, 100]}
                  domain={[0, 100]}
                  tickFormatter={(v) => `${v}%`}
                />
                <Tooltip
                  content={
                    <CustomTooltip
                      formatter={(value) => `${Number(value).toFixed(1)}%`}
                    />
                  }
                />
                <Legend
                  wrapperStyle={{ fontSize: 12, paddingTop: 12 }}
                  iconSize={10}
                  verticalAlign="bottom"
                />
                <Bar
                  dataKey="pctWinners"
                  name="Better off"
                  stackId="wl"
                  fill={PALETTE.gain}
                />
                <Bar
                  dataKey="pctUnchanged"
                  name="No change"
                  stackId="wl"
                  fill={colors.gray[300]}
                />
              </BarChart>
            </ResponsiveContainer>
          </div>
          <ChartLogo />
        </div>
      )}
      </div>
    </div>
  );
}
