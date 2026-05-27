"use client";

import { Suspense, useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import MediaCoverageTab from "../src/components/MediaCoverageTab";
import MethodologyTab from "../src/components/MethodologyTab";
import ReformTab from "../src/components/ReformTab";

const TAB_OPTIONS = [
  { id: "impact", label: "Analysis" },
  { id: "methodology", label: "Methodology" },
  { id: "media", label: "Media coverage" },
];

function getInitialTab(tabParam) {
  if (TAB_OPTIONS.some((tab) => tab.id === tabParam)) {
    return tabParam;
  }
  return "impact";
}

function Dashboard() {
  const searchParams = useSearchParams();
  const router = useRouter();

  const [activeTab, setActiveTab] = useState(() =>
    getInitialTab(searchParams.get("tab")),
  );
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const tabParam = searchParams.get("tab");
    setActiveTab(getInitialTab(tabParam));
  }, [searchParams]);

  useEffect(() => {
    async function loadData() {
      try {
        const response = await fetch(
          `${process.env.NEXT_PUBLIC_BASE_PATH}/data/fuel_duty_results.json`,
        );
        if (!response.ok) {
          throw new Error("fuel_duty_results.json not found");
        }
        const json = await response.json();
        setData(json);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    }

    loadData();
  }, []);

  function handleTabChange(tab) {
    setActiveTab(tab);
    if (tab === "impact") {
      router.replace("/", { scroll: false });
      return;
    }
    router.replace(`/?tab=${tab}`, { scroll: false });
  }

  return (
    <div className="app-shell min-h-screen">
      <header className="title-row">
        <div className="mx-auto flex max-w-[1400px] items-center justify-between px-6 py-4 md:px-8">
          <h1>Cancelling the fuel duty rise</h1>
        </div>
      </header>

      <main className="relative z-[1] mx-auto max-w-[1400px] px-6 py-10 md:px-8 md:py-12">
        <div className="animate-[fadeIn_0.4s_ease-out]">
          <p className="mb-3 text-[1.05rem] leading-relaxed text-slate-600">
            This dashboard uses{" "}
            <a
              href="https://github.com/PolicyEngine/policyengine.py"
              target="_blank"
              rel="noreferrer"
            >
              policyengine.py
            </a>{" "}
            to estimate the fiscal and household impact of cancelling the
            fuel-duty rise scheduled in the{" "}
            <a
              href="https://www.gov.uk/government/publications/budget-2025-document/budget-2025-html"
              target="_blank"
              rel="noreferrer"
            >
              Autumn Budget 2025
            </a>{" "}
            — the{" "}
            <a
              href="https://www.gov.uk/government/publications/fuel-duty-rates-for-2026-to-2027/fuel-duty-rates-2026-to-2027"
              target="_blank"
              rel="noreferrer"
            >
              staged unwinding
            </a>{" "}
            of the 5p cut and the April 2027 RPI uprating that together take
            duty to ~60p/L. In May 2026 the PM{" "}
            <a
              href="https://fleetworld.co.uk/fuel-duty-increase-delayed-until-2027-says-starmer/"
              target="_blank"
              rel="noreferrer"
            >
              postponed the September step
            </a>{" "}
            amid pump-price pressure; the figures here model the original
            schedule. The <strong>Analysis</strong> tab shows the fiscal cost
            and household impact; the <strong>Methodology</strong> tab covers
            the model, sources, and what the static analysis omits; the{" "}
            <strong>Media coverage</strong> tab links to the{" "}
            <a
              href="https://www.itv.com/watch/peston/2a4458/2a4458a0390"
              target="_blank"
              rel="noreferrer"
            >
              ITV Peston segment
            </a>
            .
          </p>
        </div>

        <div className="mb-8 mt-8 flex w-fit flex-wrap border-b-2 border-slate-200">
          {TAB_OPTIONS.map((tab) => (
            <button
              key={tab.id}
              className={`tab-button ${activeTab === tab.id ? "active" : ""}`}
              onClick={() => handleTabChange(tab.id)}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {error && (
          <p className="rounded-2xl border border-red-200 bg-red-50 p-6 text-sm text-red-700">
            Error: {error}. Run{" "}
            <code>make sync-dashboard</code> to generate the data file.
          </p>
        )}
        {loading && !error && (
          <p className="rounded-2xl border border-slate-200 bg-white p-6 text-sm text-slate-500">
            Loading data...
          </p>
        )}

        {!loading && !error && data && (
          <>
            {activeTab === "impact" && <ReformTab data={data} />}
            {activeTab === "methodology" && <MethodologyTab data={data} />}
            {activeTab === "media" && <MediaCoverageTab />}
          </>
        )}

        <footer className="mt-12 border-t border-slate-200 pt-8 text-center text-sm text-slate-500">
          <p>
            Replication code:{" "}
            <a
              href="https://github.com/PolicyEngine/cancelling-fuel-duty-rise"
              target="_blank"
              rel="noreferrer"
            >
              PolicyEngine/cancelling-fuel-duty-rise
            </a>
            .
          </p>
        </footer>
      </main>
    </div>
  );
}

export default function Page() {
  return (
    <Suspense
      fallback={<p className="p-12 text-center text-slate-500">Loading...</p>}
    >
      <Dashboard />
    </Suspense>
  );
}
