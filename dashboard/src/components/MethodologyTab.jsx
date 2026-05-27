import { fyLabel, getCitation, getMethodNote } from "../lib/dataHelpers";

export default function MethodologyTab({ data }) {
  const firstFreeze = data.headline.first_freeze_year;
  const lastYear = data.headline.last_year;
  const yearDist = data.headline.year_dist;
  const peVersion = data.model_versions.policyengine;
  const citation = getCitation(data);
  const methodNote = getMethodNote(data);

  return (
    <div className="space-y-8">
      <div className="section-card">
        <div className="eyebrow text-slate-500">Overview</div>
        <h2 className="mt-2 text-2xl font-semibold tracking-tight text-slate-900">
          What the dashboard estimates
        </h2>
        <p className="mt-4 text-sm leading-7 text-slate-600">
          This dashboard uses{" "}
          <a
            href="https://github.com/PolicyEngine/policyengine.py"
            target="_blank"
            rel="noreferrer"
          >
            policyengine.py v{peVersion}
          </a>{" "}
          on the enhanced Family Resources Survey 2023/24 to quantify the
          cost, counterfactual, and distributional impact of cancelling the
          Autumn Budget 2025 fuel-duty plan. The Budget plan ends the 5p cut
          introduced in March 2022 and resumes RPI uprating in April 2027; the
          reform we cost holds petrol and diesel duty at 52.95p/L. Fiscal
          totals are projected through {fyLabel(lastYear)}.
        </p>
        <p className="mt-4 text-sm leading-7 text-slate-600">
          Two framings sit side by side on the Impact tab:
        </p>
        <ul className="mt-2 list-disc pl-5 text-sm leading-7 text-slate-600 space-y-1">
          <li>
            <strong>Full plan</strong> — the cost of cancelling both the
            5p-cut reversal and the April 2027 RPI uprating. This is the
            headline £
            {data.headline.scrap_2027.toFixed(2)}bn for {fyLabel(2027)}.
          </li>
          <li>
            <strong>Guardian 5p-only framing</strong> — the cost of holding
            duty at 52.95p/L vs the 57.95p pre-cut rate, ignoring the RPI
            step. This is the smaller £
            {data.headline.scrap_2027 && data.tables.guardian_check
              ? data.tables.guardian_check.find((r) => r.Year === 2027)[
                  "Cost of keeping 5p cut (£bn)"
                ].toFixed(2)
              : "—"}
            bn figure that has appeared in press coverage.
          </li>
        </ul>
      </div>

      <div className="section-card">
        <div className="eyebrow text-slate-500">Simulations</div>
        <h2 className="mt-2 text-2xl font-semibold tracking-tight text-slate-900">
          How the reform is wired
        </h2>
        <p className="mt-4 text-sm leading-7 text-slate-600">
          The fuel-duty rate lives in the PolicyEngine parameter tree at{" "}
          <code>gov.hmrc.fuel_duty.petrol_and_diesel</code>. The Autumn Budget
          2025 plan is already reflected in the bundled UK model: the rate
          steps from 53.45p in {fyLabel(2026)} to{" "}
          {data.headline.baseline_rate_2027_p.toFixed(2)}p in {fyLabel(2027)},
          then rises by RPI each April out to {fyLabel(lastYear)}. The reform
          counterfactual holds the rate flat at 52.95p/L.
        </p>
        <div className="mt-4 overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-slate-200 text-left text-[11px] uppercase tracking-wide text-slate-400">
                <th className="py-2 pr-4 font-medium">Sim</th>
                <th className="py-2 pr-4 font-medium">Rate ({fyLabel(2027)})</th>
                <th className="py-2 pr-4 font-medium">Rate ({fyLabel(lastYear)})</th>
                <th className="py-2 pr-0 font-medium">Use</th>
              </tr>
            </thead>
            <tbody className="text-slate-700">
              <tr className="border-b border-slate-100">
                <td className="py-2 pr-4 font-semibold">Baseline (Budget plan)</td>
                <td className="py-2 pr-4 tabular-nums">
                  {data.headline.baseline_rate_2027_p.toFixed(2)}p
                </td>
                <td className="py-2 pr-4 tabular-nums">
                  {
                    data.tables.rate_path[data.tables.rate_path.length - 1]
                      .actual_rate_p_per_litre
                  }
                  p
                </td>
                <td className="py-2 pr-0">Current law per Autumn Budget 2025.</td>
              </tr>
              <tr className="border-b border-slate-100">
                <td className="py-2 pr-4 font-semibold">Reform (5p cut kept)</td>
                <td className="py-2 pr-4 tabular-nums">52.95p</td>
                <td className="py-2 pr-4 tabular-nums">52.95p</td>
                <td className="py-2 pr-0">Cancel the planned rise — rate held flat.</td>
              </tr>
              <tr>
                <td className="py-2 pr-4 font-semibold">RPI counterfactual</td>
                <td className="py-2 pr-4 tabular-nums">
                  {
                    data.tables.rate_path.find((r) => r.year === 2027)
                      .rpi_counterfactual_rate_p_per_litre
                  }
                  p
                </td>
                <td className="py-2 pr-4 tabular-nums">
                  {
                    data.tables.rate_path[data.tables.rate_path.length - 1]
                      .rpi_counterfactual_rate_p_per_litre
                  }
                  p
                </td>
                <td className="py-2 pr-0">
                  What duty would have been if the rate had risen by RPI every
                  April since {fyLabel(firstFreeze)}.
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <div className="grid gap-8 xl:grid-cols-2">
        <div className="section-card">
          <div className="eyebrow text-slate-500">Fiscal totals</div>
          <h3 className="mt-2 text-lg font-semibold text-slate-900">
            HMRC out-turns and OBR forecasts
          </h3>
          <p className="mt-4 text-sm leading-7 text-slate-600">
            Headline fiscal numbers (cost of cancelling, revenue at each
            counterfactual rate, fleet receipts foregone) are computed from
            HMRC road-fuel clearances and UK Tax &amp; NICs receipts out-turns
            for years that are settled, and from the March 2026 OBR fuel-duty
            receipts forecast for the projection period ({fyLabel(2025)}
            {" "}onwards). The control total for rate-difference cost
            calculations is OBR / HMRC all-road petrol + diesel litres.
          </p>
        </div>

        <div className="section-card">
          <div className="eyebrow text-slate-500">Distribution</div>
          <h3 className="mt-2 text-lg font-semibold text-slate-900">
            Household allocation
          </h3>
          <p className="mt-4 text-sm leading-7 text-slate-600">
            Distributional savings ({fyLabel(yearDist)}) apply the same
            duty-rate gap to PolicyEngine's calibrated household petrol and
            diesel litres, without post-hoc scaling. Each household's saving
            is its (petrol + diesel) litres × (baseline rate − reform rate),
            grouped by equivalised HBAI net-income decile/quintile/quartile.
            Weighted operations use the native microdf API.
          </p>
        </div>
      </div>

      <div className="section-card note-card">
        <div className="eyebrow note-eyebrow">ITV methodology note</div>
        <p className="mt-2 text-sm leading-7 note-body">{methodNote}</p>
      </div>

      <div className="grid gap-8 xl:grid-cols-2">
        <div className="section-card">
          <div className="eyebrow text-slate-500">Included</div>
          <h3 className="mt-2 text-lg font-semibold text-slate-900">
            What the model captures
          </h3>
          <ul className="mt-4 list-disc pl-5 text-sm leading-7 text-slate-600 space-y-1">
            <li>
              Static fiscal cost of cancelling the Autumn Budget 2025 fuel-duty
              plan, year by year through {fyLabel(lastYear)}
            </li>
            <li>
              Side-by-side framing of the full plan vs the Guardian 5p-only
              reading
            </li>
            <li>
              The duty rate path against a counterfactual where the rate had
              risen by RPI every April since {fyLabel(firstFreeze)}
            </li>
            <li>
              Average household saving in {fyLabel(yearDist)} by income decile,
              quintile, or quartile, in cash and as a share of net income
            </li>
            <li>
              Cumulative fleet receipts foregone since the freeze began —
              counterfactual minus actual duty receipts, summed
            </li>
          </ul>
        </div>

        <div className="section-card">
          <div className="eyebrow text-slate-500">Excluded</div>
          <h3 className="mt-2 text-lg font-semibold text-slate-900">
            What the dashboard omits
          </h3>
          <ul className="mt-4 list-disc pl-5 text-sm leading-7 text-slate-600 space-y-1">
            <li>
              <strong>Behavioural response</strong> — fuel volumes are held
              fixed across scenarios. No price-elasticity adjustment is
              applied, even though higher pump prices would reduce demand.
            </li>
            <li>
              Indirect macroeconomic effects (CPI pass-through, transport
              costs, inflation expectations)
            </li>
            <li>
              VAT receipts on fuel — the headline cost is a duty figure;
              cancelling the rise also reduces VAT-on-duty, which is not
              netted out here
            </li>
            <li>
              Carbon / air-quality externalities of holding pump prices below
              the RPI counterfactual
            </li>
            <li>
              Confidence intervals on the underlying FRS sample and HMRC /
              OBR controls
            </li>
          </ul>
        </div>
      </div>

      <div className="section-card">
        <div className="eyebrow text-slate-500">Citation</div>
        <p className="mt-2 text-sm leading-7 text-slate-600">{citation}</p>
      </div>
    </div>
  );
}
