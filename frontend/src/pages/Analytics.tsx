import React, { useState } from 'react';
import toast from 'react-hot-toast';

export const Analytics: React.FC = () => {
  const [dateRange, setDateRange] = useState('Last 30 Days (Oct 1 - Oct 30, 2024)');
  const [dropdownOpen, setDropdownOpen] = useState(false);

  const ranges = [
    'Last 7 Days (Oct 24 - Oct 30, 2024)',
    'Last 30 Days (Oct 1 - Oct 30, 2024)',
    'Last 90 Days (Aug 1 - Oct 30, 2024)',
    'Fiscal Year 2024-25 (YTD)',
  ];

  const handleExportSummary = () => {
    toast.success('Exporting Forensic Analytics Summary (PDF / CSV) with Section 65B certificate');
  };

  return (
    <div className="flex flex-col w-full pb-16 animate-in fade-in duration-200">
      <div className="flex flex-col w-full max-w-[1560px] mx-auto gap-8">
        {/* Header Section */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-6 pb-2">
          <div className="flex flex-col gap-1.5">
            <div className="flex items-center gap-3">
              <span className="inline-flex items-center px-2 py-0.5 rounded bg-surface-container-high text-on-surface-variant text-label-sm uppercase tracking-wider font-semibold">
                Forensic Intelligence Unit
              </span>
              <span className="inline-flex items-center gap-1.5 text-secondary font-code-sm font-mono font-semibold">
                <span className="w-1.5 h-1.5 rounded-full bg-secondary"></span>
                Verified Dossier Ledger
              </span>
            </div>
            <h1 className="text-display-lg text-on-surface tracking-tight font-semibold">
              Forensic Analytics &amp; Trends
            </h1>
            <p className="text-body-md text-on-surface-variant max-w-3xl leading-relaxed">
              Aggregated intelligence from NCRP portal inputs, cross-chain tracing velocities, and exchange recoveries.
            </p>
          </div>

          <div className="flex items-center gap-3 self-start md:self-auto relative">
            <div className="relative inline-block text-left">
              <button
                onClick={() => setDropdownOpen(!dropdownOpen)}
                className="flex items-center gap-2.5 h-10 px-4 rounded-lg bg-surface-container-lowest text-on-surface text-label-md font-semibold shadow-sm border border-outline-variant/60 hover:bg-surface-container-low transition-colors"
                type="button"
              >
                <span className="material-symbols-outlined text-primary text-base">calendar_today</span>
                <span>{dateRange}</span>
                <span className="material-symbols-outlined text-outline text-base">expand_more</span>
              </button>

              {dropdownOpen && (
                <div className="absolute right-0 mt-2 w-64 rounded-xl bg-surface-container-lowest shadow-xl border border-outline-variant/60 z-20 p-1.5 flex flex-col gap-1">
                  {ranges.map((r) => (
                    <button
                      key={r}
                      onClick={() => {
                        setDateRange(r);
                        setDropdownOpen(false);
                      }}
                      className={`w-full text-left px-3 py-2 rounded-lg text-body-md transition-colors flex items-center justify-between ${
                        dateRange === r
                          ? 'text-primary font-semibold bg-surface-container-low'
                          : 'text-on-surface hover:bg-surface-container'
                      }`}
                    >
                      <span>{r}</span>
                      {dateRange === r && (
                        <span className="material-symbols-outlined text-primary text-sm">check</span>
                      )}
                    </button>
                  ))}
                </div>
              )}
            </div>

            <button
              onClick={handleExportSummary}
              className="flex items-center gap-2 h-10 px-4 rounded-lg bg-surface-container-lowest text-on-surface-variant hover:text-on-surface text-label-md font-semibold shadow-sm border border-outline-variant/60 hover:bg-surface-container-low transition-colors"
              type="button"
            >
              <span className="material-symbols-outlined text-base">file_download</span>
              <span>Export Summary</span>
            </button>
          </div>
        </div>

        {/* 2-Column Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
          {/* Left Column: Fraud Typology Donut Chart */}
          <div className="lg:col-span-6 bg-surface-container-lowest rounded-xl shadow-sm border border-outline-variant/60 p-7 flex flex-col justify-between min-h-[640px]">
            <div className="flex flex-col gap-6">
              <div className="flex items-start justify-between pb-3 border-b border-outline-variant/30">
                <div className="flex flex-col gap-1">
                  <div className="flex items-center gap-2">
                    <span className="material-symbols-outlined text-primary text-xl">pie_chart</span>
                    <h2 className="text-headline-sm text-on-surface font-semibold tracking-tight">
                      Modus Operandi / Fraud Typology Distribution
                    </h2>
                  </div>
                  <p className="text-body-sm text-on-surface-variant">
                    Classified by verified complainant FIR filings across state cyber portals
                  </p>
                </div>
                <span className="font-code-sm bg-surface-container px-2.5 py-1 rounded text-on-surface-variant font-mono font-semibold">
                  TOTAL: ₹48.6 Cr
                </span>
              </div>

              <div className="flex flex-col sm:flex-row items-center justify-around gap-8 py-4">
                {/* Donut SVG */}
                <div className="relative w-56 h-56 flex-shrink-0 flex items-center justify-center">
                  <svg className="w-full h-full -rotate-90 transform" viewBox="0 0 100 100">
                    <circle
                      cx="50"
                      cy="50"
                      fill="transparent"
                      r="38"
                      stroke="#2F6DB5"
                      strokeDasharray="90.7 238.76"
                      strokeDashoffset="0"
                      strokeWidth="15"
                    ></circle>
                    <circle
                      cx="50"
                      cy="50"
                      fill="transparent"
                      r="38"
                      stroke="#33567f"
                      strokeDasharray="64.5 238.76"
                      strokeDashoffset="-90.7"
                      strokeWidth="15"
                    ></circle>
                    <circle
                      cx="50"
                      cy="50"
                      fill="transparent"
                      r="38"
                      stroke="#D9901A"
                      strokeDasharray="43.0 238.76"
                      strokeDashoffset="-155.2"
                      strokeWidth="15"
                    ></circle>
                    <circle
                      cx="50"
                      cy="50"
                      fill="transparent"
                      r="38"
                      stroke="#C8504B"
                      strokeDasharray="26.3 238.76"
                      strokeDashoffset="-198.2"
                      strokeWidth="15"
                    ></circle>
                    <circle
                      cx="50"
                      cy="50"
                      fill="transparent"
                      r="38"
                      stroke="#6ad9c7"
                      strokeDasharray="14.3 238.76"
                      strokeDashoffset="-224.5"
                      strokeWidth="15"
                    ></circle>
                  </svg>
                  <div className="absolute inset-0 flex flex-col items-center justify-center text-center pointer-events-none">
                    <span className="text-label-sm uppercase tracking-wider text-outline font-semibold">Analyzed</span>
                    <span className="text-headline-lg text-on-surface font-bold">1,842</span>
                    <span className="text-body-sm text-on-surface-variant font-medium">FIR Traces</span>
                  </div>
                </div>

                {/* Legend & Breakdown */}
                <div className="flex flex-col gap-3 w-full sm:max-w-xs">
                  <div className="flex items-center justify-between p-2.5 rounded-lg bg-surface-container-low transition-colors hover:bg-surface-container border border-outline-variant/30">
                    <div className="flex items-center gap-2.5">
                      <span className="w-3 h-3 rounded-full bg-primary flex-shrink-0"></span>
                      <div className="flex flex-col">
                        <span className="text-label-md text-on-surface font-semibold">Telegram Task Scam</span>
                        <span className="font-code-sm text-on-surface-variant font-mono">₹18.4 Cr</span>
                      </div>
                    </div>
                    <span className="font-code-md font-semibold text-primary font-mono">38%</span>
                  </div>

                  <div className="flex items-center justify-between p-2.5 rounded-lg bg-surface-container-low transition-colors hover:bg-surface-container border border-outline-variant/30">
                    <div className="flex items-center gap-2.5">
                      <span className="w-3 h-3 rounded-full bg-tertiary flex-shrink-0"></span>
                      <div className="flex flex-col">
                        <span className="text-label-md text-on-surface font-semibold">Fake Investment App</span>
                        <span className="font-code-sm text-on-surface-variant font-mono">₹14.8 Cr</span>
                      </div>
                    </div>
                    <span className="font-code-md font-semibold text-tertiary font-mono">27%</span>
                  </div>

                  <div className="flex items-center justify-between p-2.5 rounded-lg bg-surface-container-low transition-colors hover:bg-surface-container border border-outline-variant/30">
                    <div className="flex items-center gap-2.5">
                      <span className="w-3 h-3 rounded-full bg-[#D9901A] flex-shrink-0"></span>
                      <div className="flex flex-col">
                        <span className="text-label-md text-on-surface font-semibold">Digital Arrest Impersonation</span>
                        <span className="font-code-sm text-on-surface-variant font-mono">₹9.2 Cr</span>
                      </div>
                    </div>
                    <span className="font-code-md font-semibold text-[#D9901A] font-mono">18%</span>
                  </div>

                  <div className="flex items-center justify-between p-2.5 rounded-lg bg-surface-container-low transition-colors hover:bg-surface-container border border-outline-variant/30">
                    <div className="flex items-center gap-2.5">
                      <span className="w-3 h-3 rounded-full bg-[#C8504B] flex-shrink-0"></span>
                      <div className="flex flex-col">
                        <span className="text-label-md text-on-surface font-semibold">Sextortion / Blackmail</span>
                        <span className="font-code-sm text-on-surface-variant font-mono">₹4.1 Cr</span>
                      </div>
                    </div>
                    <span className="font-code-md font-semibold text-[#C8504B] font-mono">11%</span>
                  </div>

                  <div className="flex items-center justify-between p-2.5 rounded-lg bg-surface-container-low transition-colors hover:bg-surface-container border border-outline-variant/30">
                    <div className="flex items-center gap-2.5">
                      <span className="w-3 h-3 rounded-full bg-secondary-fixed-dim flex-shrink-0"></span>
                      <div className="flex flex-col">
                        <span className="text-label-md text-on-surface font-semibold">Phishing / Drainers</span>
                        <span className="font-code-sm text-on-surface-variant font-mono">₹2.1 Cr</span>
                      </div>
                    </div>
                    <span className="font-code-md font-semibold text-secondary font-mono">6%</span>
                  </div>
                </div>
              </div>
            </div>

            <div className="mt-6 pt-4 bg-surface-container-low border border-outline-variant/40 rounded-lg p-3.5 flex items-start gap-3">
              <span className="material-symbols-outlined text-primary text-lg flex-shrink-0 mt-0.5">info</span>
              <p className="text-body-sm text-on-surface-variant leading-relaxed">
                Telegram job scams remain the highest volume vector across northern and western cyber police ranges, typically utilizing fast multi-layer mule chains prior to automated exchange aggregation.
              </p>
            </div>
          </div>

          {/* Right Column: Speed Comparison & Top VASP Inflows */}
          <div className="lg:col-span-6 flex flex-col gap-8">
            {/* Speed Reduction Card */}
            <div className="bg-surface-container-lowest rounded-xl shadow-sm border border-outline-variant/60 p-7 flex flex-col justify-between">
              <div className="flex flex-col gap-5">
                <div className="flex items-start justify-between">
                  <div className="flex flex-col gap-1">
                    <div className="flex items-center gap-2">
                      <span className="material-symbols-outlined text-secondary text-xl">speed</span>
                      <h2 className="text-headline-sm text-on-surface font-semibold tracking-tight">
                        Average Turnaround to Identify VASP
                      </h2>
                    </div>
                    <p className="text-body-sm text-on-surface-variant">
                      Benchmarked against traditional bank liaisoning &amp; unassisted explorer lookups
                    </p>
                  </div>
                  <span className="inline-flex items-center gap-1 px-3 py-1 rounded-full bg-secondary-container/40 text-on-secondary-container text-label-md font-semibold">
                    <span className="material-symbols-outlined text-sm">trending_down</span>
                    94% Speed Reduction
                  </span>
                </div>

                <div className="flex flex-col gap-5 my-2">
                  <div className="flex flex-col gap-2">
                    <div className="flex justify-between items-center text-on-surface">
                      <div className="flex items-center gap-2">
                        <span className="text-label-md font-semibold">Manual Investigation</span>
                        <span className="text-body-sm text-outline">(Multi-hop explorers + bank letters)</span>
                      </div>
                      <span className="font-code-md font-semibold text-outline font-mono">72 hours (3 days)</span>
                    </div>
                    <div className="w-full bg-surface-container h-8 rounded-lg overflow-hidden flex items-center p-1 border border-outline-variant/30">
                      <div className="bg-outline-variant h-full rounded transition-all duration-700 ease-out flex items-center justify-end pr-3 w-full">
                        <span className="font-code-sm font-semibold text-on-surface font-mono">4,320 mins</span>
                      </div>
                    </div>
                  </div>

                  <div className="flex flex-col gap-2">
                    <div className="flex justify-between items-center text-on-surface">
                      <div className="flex items-center gap-2">
                        <span className="text-label-md font-semibold text-primary">ChainNetra Automated Tracing</span>
                        <span className="text-body-sm text-secondary font-medium">(Heuristic cluster attribution)</span>
                      </div>
                      <span className="font-code-md font-semibold text-secondary font-mono">38 minutes</span>
                    </div>
                    <div className="w-full bg-surface-container h-8 rounded-lg overflow-hidden flex items-center p-1 border border-outline-variant/30">
                      <div
                        className="bg-gradient-to-r from-primary to-secondary h-full rounded transition-all duration-700 ease-out flex items-center px-3"
                        style={{ width: '12%' }}
                      >
                        <span className="font-code-sm font-bold text-on-primary whitespace-nowrap font-mono">38m</span>
                      </div>
                    </div>
                  </div>
                </div>

                <div className="p-3 bg-secondary-container/20 border border-secondary/30 rounded-lg flex items-center justify-between">
                  <span className="text-body-sm text-on-surface font-medium">
                    Critical Window: Preserving evidence before off-ramp withdrawal
                  </span>
                  <span className="font-code-sm font-semibold text-secondary font-mono">Safe Threshold: &lt; 2h</span>
                </div>
              </div>

              <div className="mt-4 pt-3 border-t border-outline-variant/30 flex items-start gap-2.5">
                <span className="material-symbols-outlined text-outline text-base mt-0.5">verified</span>
                <p className="text-body-sm text-on-surface-variant leading-relaxed">
                  Enables Section 91 CrPC notice dispatch well within the critical 2-hour exchange withdrawal window.
                </p>
              </div>
            </div>

            {/* Top Recipient Exchanges */}
            <div className="bg-surface-container-lowest rounded-xl shadow-sm border border-outline-variant/60 p-7 flex flex-col justify-between">
              <div className="flex flex-col gap-5">
                <div className="flex items-start justify-between">
                  <div className="flex flex-col gap-1">
                    <div className="flex items-center gap-2">
                      <span className="material-symbols-outlined text-tertiary text-xl">account_balance</span>
                      <h2 className="text-headline-sm text-on-surface font-semibold tracking-tight">
                        Top Recipient Exchanges for Fraudulent Inflows
                      </h2>
                    </div>
                    <p className="text-body-sm text-on-surface-variant">
                      Final identified VASP depository clusters for seized and flagged wallets
                    </p>
                  </div>
                  <span className="text-label-sm uppercase tracking-wider bg-surface-container px-2.5 py-1 rounded text-on-surface font-semibold">
                    Active LEAF Nodes
                  </span>
                </div>

                <div className="flex flex-col gap-3.5 my-1">
                  <div className="flex flex-col gap-1.5">
                    <div className="flex justify-between items-center">
                      <div className="flex items-center gap-2">
                        <span className="text-label-md font-semibold text-on-surface">DemoX Global</span>
                        <span className="text-label-sm px-1.5 py-0.5 bg-surface-container text-on-surface-variant rounded">
                          Nodal Liaison SLA: 45m
                        </span>
                      </div>
                      <div className="flex items-center gap-3">
                        <span className="font-code-sm text-on-surface-variant font-mono">₹14.5 Cr</span>
                        <span className="font-code-sm font-semibold text-on-surface w-10 text-right font-mono">32%</span>
                      </div>
                    </div>
                    <div className="w-full bg-surface-container h-2.5 rounded-full overflow-hidden">
                      <div className="bg-primary h-full rounded-full" style={{ width: '32%' }}></div>
                    </div>
                  </div>

                  <div className="flex flex-col gap-1.5">
                    <div className="flex justify-between items-center">
                      <div className="flex items-center gap-2">
                        <span className="text-label-md font-semibold text-on-surface">Binance Global</span>
                        <span className="text-label-sm px-1.5 py-0.5 bg-surface-container text-on-surface-variant rounded">
                          Interpol Orange Notice
                        </span>
                      </div>
                      <div className="flex items-center gap-3">
                        <span className="font-code-sm text-on-surface-variant font-mono">₹12.8 Cr</span>
                        <span className="font-code-sm font-semibold text-on-surface w-10 text-right font-mono">28%</span>
                      </div>
                    </div>
                    <div className="w-full bg-surface-container h-2.5 rounded-full overflow-hidden">
                      <div className="bg-tertiary-container h-full rounded-full" style={{ width: '28%' }}></div>
                    </div>
                  </div>

                  <div className="flex flex-col gap-1.5">
                    <div className="flex justify-between items-center">
                      <div className="flex items-center gap-2">
                        <span className="text-label-md font-semibold text-on-surface">Bybit</span>
                        <span className="text-label-sm px-1.5 py-0.5 bg-surface-container text-on-surface-variant rounded">
                          P2P Escrow Focus
                        </span>
                      </div>
                      <div className="flex items-center gap-3">
                        <span className="font-code-sm text-on-surface-variant font-mono">₹8.4 Cr</span>
                        <span className="font-code-sm font-semibold text-on-surface w-10 text-right font-mono">18%</span>
                      </div>
                    </div>
                    <div className="w-full bg-surface-container h-2.5 rounded-full overflow-hidden">
                      <div className="bg-[#D9901A] h-full rounded-full" style={{ width: '18%' }}></div>
                    </div>
                  </div>

                  <div className="flex flex-col gap-1.5">
                    <div className="flex justify-between items-center">
                      <div className="flex items-center gap-2">
                        <span className="text-label-md font-semibold text-on-surface">WazirX</span>
                        <span className="text-label-sm px-1.5 py-0.5 bg-secondary-container/40 text-secondary rounded font-semibold">
                          FIU-IND Registered
                        </span>
                      </div>
                      <div className="flex items-center gap-3">
                        <span className="font-code-sm text-on-surface-variant font-mono">₹5.2 Cr</span>
                        <span className="font-code-sm font-semibold text-on-surface w-10 text-right font-mono">11%</span>
                      </div>
                    </div>
                    <div className="w-full bg-surface-container h-2.5 rounded-full overflow-hidden">
                      <div className="bg-secondary h-full rounded-full" style={{ width: '11%' }}></div>
                    </div>
                  </div>

                  <div className="flex flex-col gap-1.5">
                    <div className="flex justify-between items-center">
                      <span className="text-label-md text-on-surface-variant">Other Domestic &amp; Offshore VASPs</span>
                      <div className="flex items-center gap-3">
                        <span className="font-code-sm text-on-surface-variant font-mono">₹4.9 Cr</span>
                        <span className="font-code-sm font-semibold text-on-surface w-10 text-right font-mono">11%</span>
                      </div>
                    </div>
                    <div className="w-full bg-surface-container h-2.5 rounded-full overflow-hidden">
                      <div className="bg-outline-variant h-full rounded-full" style={{ width: '11%' }}></div>
                    </div>
                  </div>
                </div>
              </div>

              <div className="mt-4 pt-3 border-t border-outline-variant/30 flex items-start gap-2.5">
                <span className="material-symbols-outlined text-outline text-base mt-0.5">policy</span>
                <p className="text-body-sm text-on-surface-variant leading-relaxed">
                  89% of fraudulent outflows terminate at top 4 exchanges with registered nodal channels.
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Evidentiary Integrity Footer */}
        <div className="flex items-center justify-between py-3 px-4 rounded-xl bg-surface-container-low text-on-surface-variant text-body-sm border border-outline-variant/40">
          <div className="flex items-center gap-2">
            <span className="material-symbols-outlined text-base text-secondary">gavel</span>
            <span>Evidentiary integrity preserved. Hash verification conforms with Section 65B Indian Evidence Act standards.</span>
          </div>
          <span className="font-code-sm text-outline font-mono">BATCH_VERIFY: SHA256#a7f920...9ec1</span>
        </div>
      </div>
    </div>
  );
};
