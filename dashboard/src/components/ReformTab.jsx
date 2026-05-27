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

  const [grouping, setGrouping] = useState("deciles");
  const [impactMode, setImpactMode] = useState("abs");
  const distribution = useMemo(
    () => getDistribution(data, grouping),
    [data, grouping],
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
            The Autumn Budget 2025 plan would let the 5p-per-litre cut introduced
            in March 2022 expire and apply RPI uprating in April 2027, taking
            petrol and diesel duty from 52.95p/L to {headline.baseline_rate_2027_p.toFixed(2)}p/L
            in one step and continuing to uprate by RPI through {fyLabel(lastYear)}.
            This page quantifies the cost of cancelling that plan and keeping
            duty at 52.95p/L, the household-level distribution of those savings
            in {fyLabel(yearDist)}, and how the policy compares to the
            long-running freeze of UK fuel duty going back to {fyLabel(firstFreeze)}.
            Headline fiscal totals use HMRC/OBR road-fuel clearances and
            receipts; distributional savings apply the same duty-rate gap to
            PolicyEngine's calibrated household litres.
          </>
        }
      />

      {/* Headline metric cards */}
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <div className="metric-card">
          <div className="text-xs font-medium uppercase tracking-[0.08em] text-slate-500">
            Cancel full plan ({fyLabel(2027)})
          </div>
          <div className="mt-2 text-3xl font-bold tracking-tight text-slate-900 tabular-nums">
            {formatBn(headline.scrap_2027)}
          </div>
          <div className="mt-1 text-sm text-slate-500">
            Cost to Treasury of holding duty at 52.95p/L vs the {fyLabel(2027)} Budget plan.
          </div>
        </div>
        <div className="metric-card">
          <div className="text-xs font-medium uppercase tracking-[0.08em] text-slate-500">
            Cancel full plan ({fyLabel(lastYear)})
          </div>
          <div className="mt-2 text-3xl font-bold tracking-tight text-slate-900 tabular-nums">
            {formatBn(headline.scrap_2029)}
          </div>
          <div className="mt-1 text-sm text-slate-500">
            By {fyLabel(lastYear)} the gap widens as the RPI counterfactual
            grows ({headline.baseline_rate_2027_p.toFixed(2)}p planned in 2027,
            52.95p kept).
          </div>
        </div>
        <div className="metric-card">
          <div className="text-xs font-medium uppercase tracking-[0.08em] text-slate-500">
            Extend 5p cut only ({fyLabel(2027)})
          </div>
          <div className="mt-2 text-3xl font-bold tracking-tight text-slate-900 tabular-nums">
            {formatBn(guardian2027.cost5pBn)}
          </div>
          <div className="mt-1 text-sm text-slate-500">
            Guardian framing: 52.95p vs 57.95p only — excludes the April 2027
            RPI step.
          </div>
        </div>
        <div className="metric-card">
          <div className="text-xs font-medium uppercase tracking-[0.08em] text-slate-500">
            Fleet receipts foregone since {fyLabel(firstFreeze)}
          </div>
          <div className="mt-2 text-3xl font-bold tracking-tight text-slate-900 tabular-nums">
            {formatBn(headline.fleet_cumulative)}
          </div>
          <div className="mt-1 text-sm text-slate-500">
            Cumulative gap between counterfactual RPI uprating and actual
            duty receipts, {fyLabel(firstFreeze)} – {fyLabel(2026)}.
          </div>
        </div>
      </div>

      {/* What is changing */}
      <div className="section-card">
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

      {/* Annual cost — full plan vs Guardian 5p framing */}
      <div className="grid gap-8 xl:grid-cols-2">
        <div className="section-card">
          <SectionHeading
            title="Cost of cancelling the full plan, by year"
            description={`Difference between baseline revenue at the planned duty rate and reform revenue at the frozen 52.95p/L rate. ${fyLabel(2026)}–${fyLabel(lastYear)} only — earlier years already match the reform.`}
          />
          <div className="h-[380px] w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={scrap5p}>
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
                <Bar dataKey="costBn" name="Cost to Treasury" radius={[6, 6, 0, 0]}>
                  {scrap5p.map((row, i) => (
                    <Cell
                      key={`c-${i}`}
                      fill={row.costBn > 0 ? PALETTE.loss : PALETTE.gain}
                    />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
          <ChartLogo />
        </div>

        <div className="section-card">
          <SectionHeading
            title="Guardian 5p-only framing, by year"
            description="Cost of holding duty at 52.95p/L against the pre-2022 57.95p rate only — ignores the April 2027 RPI step that the full Budget plan also unwinds."
          />
          <div className="h-[380px] w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={guardian}>
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
                  name="Cost of keeping 5p cut"
                  fill={PALETTE.gainSoft}
                  radius={[6, 6, 0, 0]}
                />
              </BarChart>
            </ResponsiveContainer>
          </div>
          <ChartLogo />
        </div>
      </div>

      {/* Rate path chart */}
      <div className="section-card">
        <SectionHeading
          title="Duty rate path — actual vs RPI counterfactual"
          description={`What petrol and diesel duty would have been if the rate had risen by RPI every April since ${fyLabel(firstFreeze)}, compared to the rate actually charged.`}
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

      {/* OBR-style revenue chart */}
      {revenueSeries.length > 0 && (
        <div className="section-card">
          <SectionHeading
            title="Fuel duty receipts — actual vs RPI counterfactual"
            description={`Annual UK fuel duty receipts under the frozen duty rate (HMRC out-turns to ${fyLabel(2024)}; OBR March 2026 forecast thereafter) compared to receipts under an RPI-uprated counterfactual. The shaded gap is the cumulative £${headline.fleet_cumulative.toFixed(0)}bn of receipts foregone since ${fyLabel(firstFreeze)}.`}
          />
          <div className="h-[420px] w-full">
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

      {/* Distributional chart */}
      <div className="section-card">
        <div className="mb-4 flex flex-wrap items-start justify-between gap-3">
          <SectionHeading
            title={`Average annual saving by income group (${fyLabel(yearDist)})`}
            description={
              impactMode === "abs"
                ? "Mean saving in cash terms — household petrol and diesel litres times the duty-rate gap, averaged across all households in each group."
                : "Mean saving as a share of net income — same numerator, divided by household net income."
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
    </div>
  );
}
