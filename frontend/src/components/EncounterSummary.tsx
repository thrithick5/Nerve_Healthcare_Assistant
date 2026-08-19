import { getEncounterInfo } from '../utils/clinicalData'

interface EncounterSummaryProps {
  specialty: string
  dark?: boolean
}

const TRIAGE_STYLES: Record<string, { bg: string; text: string; ring: string; label: string }> = {
  emergency: {
    bg: 'bg-red-50 dark:bg-red-950/30',
    text: 'text-red-700 dark:text-red-400',
    ring: 'border-red-200 dark:border-red-900/50',
    label: 'Emergency — seek immediate care',
  },
  urgent: {
    bg: 'bg-amber-50 dark:bg-amber-950/30',
    text: 'text-amber-700 dark:text-amber-400',
    ring: 'border-amber-200 dark:border-amber-900/50',
    label: 'Urgent — see a specialist soon',
  },
  routine: {
    bg: 'bg-emerald-50 dark:bg-emerald-950/30',
    text: 'text-emerald-700 dark:text-emerald-400',
    ring: 'border-emerald-200 dark:border-emerald-900/50',
    label: 'Routine — primary care follow-up',
  },
}

export function EncounterSummary({ specialty, dark }: EncounterSummaryProps) {
  const info = getEncounterInfo(specialty)
  const triage = TRIAGE_STYLES[info.triage]

  return (
    <div className={`rounded-2xl border ${triage.ring} ${triage.bg} overflow-hidden`}>
      <div className={`px-4 py-3 border-b ${dark ? 'border-[#383838]' : 'border-gray-200'} flex items-center justify-between`}>
        <div className="flex items-center gap-2">
          <svg className={`w-4 h-4 ${triage.text}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
          </svg>
          <h4 className={`text-sm font-semibold ${triage.text}`}>Encounter Summary — {info.label}</h4>
        </div>
        <span className={`text-[11px] font-medium px-2.5 py-1 rounded-full ${triage.bg} ${triage.text}`}>
          {triage.label}
        </span>
      </div>

      <div className="p-4 space-y-4">
        <div>
          <h5 className={`text-xs font-semibold uppercase tracking-wide mb-2 ${dark ? 'text-neutral-400' : 'text-gray-500'}`}>
            Red flag symptoms — go to ER immediately if any apply
          </h5>
          <ul className="space-y-1.5">
            {info.redFlags.map((flag, i) => (
              <li key={i} className="flex items-start gap-2 text-sm">
                <svg className={`w-4 h-4 shrink-0 mt-0.5 ${triage.text}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                </svg>
                <span className={dark ? 'text-neutral-300' : 'text-gray-700'}>{flag}</span>
              </li>
            ))}
          </ul>
        </div>

        <div>
          <h5 className={`text-xs font-semibold uppercase tracking-wide mb-2 ${dark ? 'text-neutral-400' : 'text-gray-500'}`}>
            Questions to ask your doctor
          </h5>
          <ul className="space-y-1.5">
            {info.questions.map((q, i) => (
              <li key={i} className="flex items-start gap-2 text-sm">
                <span className={`w-5 h-5 rounded-full flex items-center justify-center text-[11px] font-bold shrink-0 ${triage.bg} ${triage.text}`}>
                  {i + 1}
                </span>
                <span className={dark ? 'text-neutral-300' : 'text-gray-700'}>{q}</span>
              </li>
            ))}
          </ul>
        </div>

        <p className={`text-xs italic ${dark ? 'text-neutral-500' : 'text-gray-500'}`}>
          For informational purposes only. Not a diagnosis. If symptoms are severe, call 112 / 108 / 911 or go to the nearest ER.
        </p>
      </div>
    </div>
  )
}