import type { FacilityData } from '../types'
import { FacilityCard } from './FacilityCard'

interface FacilityRecommendationsProps {
  facilityData: FacilityData
}

export function FacilityRecommendations({ facilityData }: FacilityRecommendationsProps) {
  const { specialty, facilities, search_url } = facilityData
  if (!facilities || facilities.length === 0) return null

  return (
    <div className="mt-3 border border-gray-200 dark:border-[#383838] rounded-2xl overflow-hidden bg-gray-50 dark:bg-[#1a1a1a]">
      <div className="px-4 py-3 bg-gradient-to-r from-primary-500 to-primary-600 dark:from-primary-600 dark:to-primary-700">
        <div className="flex items-center gap-2">
          <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
          </svg>
          <h3 className="text-sm font-semibold text-white">
            Healthcare Facilities — {specialty.charAt(0).toUpperCase() + specialty.slice(1)}
          </h3>
        </div>
      </div>
      <div className="p-3 space-y-2">
        {facilities.map((facility, index) => (
          <FacilityCard key={index} facility={facility} index={index + 1} />
        ))}
      </div>
      {search_url && (
        <div className="px-4 pb-3">
          <a
            href={search_url}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center justify-center gap-2 w-full py-2 text-xs font-medium text-primary-600 dark:text-primary-400 border border-primary-200 dark:border-primary-800 rounded-lg hover:bg-primary-50 dark:hover:bg-primary-900/20 transition-colors"
          >
            <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
            Search all {specialty} facilities on Google Maps
          </a>
        </div>
      )}
      <div className="px-4 pb-3">
        <div className="flex items-start gap-2 p-2.5 rounded-lg bg-amber-50 dark:bg-amber-900/10 border border-amber-200 dark:border-amber-800/30">
          <svg className="w-4 h-4 text-amber-500 shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
          </svg>
          <p className="text-xs text-amber-700 dark:text-amber-400">
            <strong>Emergency?</strong> Call 112 / 108 / 911 for life-threatening conditions. Always consult a healthcare professional.
          </p>
        </div>
      </div>
    </div>
  )
}
