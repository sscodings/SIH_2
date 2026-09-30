import React from 'react';
import { useNavigate } from 'react-router-dom';
import { X, ChevronLeft, ChevronRight, PlayCircle, CheckCircle, Sparkles } from 'lucide-react';
import { useAppStore } from '../stores/useAppStore';

interface TourStep {
  title: string;
  description: string;
  targetPath?: string;
  badge?: string;
}

export const TOUR_STEPS: TourStep[] = [
  {
    title: 'Welcome to ChainNetra',
    description: 'Victims of investment scams, task fraud, and cybercrime report burner wallets. Tracing manual multi-chain flows used to take days of scarce expert labor. ChainNetra turns this into an automated, minutes-long workflow.',
    badge: '1 / 17'
  },
  {
    title: 'Forensic Command Center KPIs',
    description: 'Track open cyber cases, complaints received today, and the signature "time-to-VASP" metric showing how rapidly illicit proceeds are pinpointed to a freezing corridor.',
    targetPath: '/',
    badge: '2 / 17'
  },
  {
    title: 'Operating Mode Indicator',
    description: 'The amber badge indicates deterministic DEMO DATA (fully runnable offline). Toggle to LIVE mode in settings to connect live TronGrid, Etherscan, and Esplora public APIs.',
    badge: '3 / 17'
  },
  {
    title: 'Complaint Inbox (NCRP / SAHYOG)',
    description: 'Simulates official citizen cybercrime reports. Try clicking "Simulate Incoming Complaint" or bulk uploading a CSV with automated chain detection (Tron, Bitcoin, EVM).',
    targetPath: '/inbox',
    badge: '4 / 17'
  },
  {
    title: 'Case Workspace & Trace Controls',
    description: 'Select max depth, USD minimum threshold, and taint models (Haircut, FIFO, or Poison). Toggle "Stop at first VASP" to focus on the nearest cashout exchange.',
    targetPath: '/cases/1',
    badge: '5 / 17'
  },
  {
    title: 'Live Radar Sweep & Event Stream',
    description: 'When a trace begins, a rotating radar sweep activates and nodes stream in live via WebSockets as hops, mules, and bridges are uncovered.',
    targetPath: '/cases/1',
    badge: '6 / 17'
  },
  {
    title: 'Fund-Flow Graph Legend',
    description: 'Node border colors represent risk levels (green=low, amber=medium, coral=critical). Edge thickness scales with amount, and flow particles animate in the direction of the money.',
    targetPath: '/cases/1',
    badge: '7 / 17'
  },
  {
    title: 'Nearest VASP Card & Confidence',
    description: 'When a VASP is reached, a dedicated card slides in with attribution confidence breakdown (label source weight, evidence strength, cluster support, hop decay).',
    targetPath: '/cases/1',
    badge: '8 / 17'
  },
  {
    title: 'Node Inspector & Behavioral Risk',
    description: 'Click any node to inspect 12 behavioral features (fan-in, fan-out, pass-through velocity, mixer exposure) and AI/ML anomaly risk factors.',
    targetPath: '/cases/1',
    badge: '9 / 17'
  },
  {
    title: 'Cross-Chain Bridge Detection',
    description: 'Automated bridge matching connects source chain deposits to destination chain releases within tolerance, displayed as violet dashed edges.',
    targetPath: '/cross-chain',
    badge: '10 / 17'
  },
  {
    title: 'Money Flow Replay Timeline',
    description: 'Use the bottom chronological scrubber with 1× to 8× speed control to replay the exact timeline of how victims funds traversed the blockchain.',
    targetPath: '/cases/1',
    badge: '11 / 17'
  },
  {
    title: 'VASP Freeze Request Composer',
    description: 'Auto-populate formal law enforcement freeze requests, citing transaction hashes, loss figures, and legal sections (IT Act / CrPC) with live PDF generation.',
    targetPath: '/vasps',
    badge: '12 / 17'
  },
  {
    title: 'Standardized Investigation Reports',
    description: 'Generate tamper-evident A4 forensic dossiers complete with an executive summary, transaction tables, and a cryptographic QR verification code.',
    targetPath: '/reports',
    badge: '13 / 17'
  },
  {
    title: 'Case Linking & Syndicate Board',
    description: 'Evidence-board style view with red-thread connectors showing when multiple separate complaints converge on a shared collector wallet or syndicate.',
    targetPath: '/linking',
    badge: '14 / 17'
  },
  {
    title: 'Watchlist & Live Movement Alerts',
    description: 'Monitor dormant crime balances. Test the "Simulate Movement" button to see instant alerts dispatch across toasts, feeds, and webhooks.',
    targetPath: '/watchlist',
    badge: '15 / 17'
  },
  {
    title: 'APIs & Webhook SIEM Connectors',
    description: 'REST endpoints, API keys, and HMAC-SHA256 signed webhooks allow seamless integration into state police command centers and SIEM platforms.',
    targetPath: '/integrations',
    badge: '16 / 17'
  },
  {
    title: 'Ready for Live Walkthrough',
    description: 'You are now ready to operate ChainNetra! Click "Launch Case Zero Guided Demo" to run the investment scam scenario with live narration captions.',
    badge: '17 / 17'
  }
];

export const GuidedTour: React.FC = () => {
  const navigate = useNavigate();
  const { tourActive, currentTourStep, endTour, setTourStep } = useAppStore();

  if (!tourActive) return null;

  const step = TOUR_STEPS[currentTourStep];
  const isLast = currentTourStep === TOUR_STEPS.length - 1;

  const handleNext = () => {
    if (isLast) {
      endTour();
      navigate('/cases/1');
    } else {
      const nextIdx = currentTourStep + 1;
      setTourStep(nextIdx);
      if (TOUR_STEPS[nextIdx].targetPath) {
        navigate(TOUR_STEPS[nextIdx].targetPath!);
      }
    }
  };

  const handleBack = () => {
    if (currentTourStep > 0) {
      const prevIdx = currentTourStep - 1;
      setTourStep(prevIdx);
      if (TOUR_STEPS[prevIdx].targetPath) {
        navigate(TOUR_STEPS[prevIdx].targetPath!);
      }
    }
  };

  return (
    <div className="fixed inset-0 z-50 pointer-events-none flex items-end justify-center pb-8 px-4">
      <div className="pointer-events-auto w-full max-w-lg bg-panel border-2 border-amber/60 rounded-xl shadow-2xl p-5 animate-in slide-in-from-bottom-5 duration-200">
        {/* Header */}
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-amber animate-pulse" />
            <span className="text-[11px] font-mono text-amber font-bold tracking-wider">
              GUIDED WALKTHROUGH TOUR {step.badge && `• ${step.badge}`}
            </span>
          </div>
          <button 
            onClick={endTour}
            className="text-text-muted hover:text-text-primary p-1 rounded"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Content */}
        <h3 className="text-base font-bold text-text-primary mb-1.5">{step.title}</h3>
        <p className="text-xs text-text-muted leading-relaxed mb-4">
          {step.description}
        </p>

        {/* Progress dots & Actions */}
        <div className="flex items-center justify-between pt-2 border-t border-hairline">
          {/* Dots */}
          <div className="flex items-center gap-1">
            {TOUR_STEPS.map((_, i) => (
              <span
                key={i}
                className={`h-1.5 rounded-full transition-all ${
                  i === currentTourStep 
                    ? 'w-4 bg-amber' 
                    : (i < currentTourStep ? 'w-1.5 bg-amber/50' : 'w-1.5 bg-hairline')
                }`}
              />
            ))}
          </div>

          {/* Navigation Buttons */}
          <div className="flex items-center gap-2">
            <button
              onClick={endTour}
              className="px-2.5 py-1 text-xs text-text-muted hover:text-text-primary transition-colors"
            >
              Skip
            </button>

            {currentTourStep > 0 && (
              <button
                onClick={handleBack}
                className="px-3 py-1.5 rounded bg-raised hover:bg-hairline text-xs text-text-primary transition-colors flex items-center gap-1"
              >
                <ChevronLeft className="w-3.5 h-3.5" /> Back
              </button>
            )}

            <button
              onClick={handleNext}
              className="px-3.5 py-1.5 rounded bg-amber text-ink font-bold text-xs hover:bg-amber-400 transition-colors flex items-center gap-1 shadow"
            >
              {isLast ? (
                <>Launch Case Zero Demo <PlayCircle className="w-3.5 h-3.5" /></>
              ) : (
                <>Next <ChevronRight className="w-3.5 h-3.5" /></>
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
