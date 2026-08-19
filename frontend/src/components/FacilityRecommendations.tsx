import { useState } from 'react'
import type { Facility, FacilityData } from '../types'
import { FacilityCard } from './FacilityCard'
import { HospitalMap } from './HospitalMap'
import { EncounterSummary } from './EncounterSummary'

interface FacilityRecommendationsProps {
  facilityData: FacilityData
  userLat?: number
  userLng?: number
  dark?: boolean
}

export function FacilityRecommendations({ facilityData, userLat, userLng, dark }: FacilityRecommendationsProps) {
  const { specialty, facilities, search_url } = facilityData
  const [selectedFacility, setSelectedFacility] = useState<Facility | null>(null)

  if (!facilities || facilities.length === 0) return null

  const hasCoords = facilities.some((f) => f.latitude !== undefined && f.longitude !== undefined)
  const userCoordsKnown = userLat !== undefined && userLng !== undefined
  const mapUserLat = userLat ?? facilityData.latitude
  const mapUserLng = userLng ?? facilityData.longitude

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

      <div className="p-3 space-y-3">
        <EncounterSummary specialty={specialty} dark={dark} />

        {hasCoords && (
          <HospitalMap
            facilities={facilities}
            userLat={mapUserLat}
            userLng={mapUserLng}
            selectedFacility={selectedFacility}
            onFacilitySelect={setSelectedFacility}
            dark={dark}
          />
        )}

        {!hasCoords && (
          <div className={`flex items-start gap-2 p-3 rounded-xl text-sm border ${dark ? 'border-[#383838] bg-[#1e1e1e]' : 'border-gray-200 bg-white'}`}>
            <svg className="w-4 h-4 shrink-0 mt-0.5 text-primary-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
            </svg>
            <div>
              <p className={dark ? 'text-neutral-300' : 'text-gray-700'}>
                {userCoordsKnown ? 'Select a facility below to view it on the map.' : 'Enable location access for a map of nearby facilities.'}
              </p>
              <p className={`mt-0.5 text-xs ${dark ? 'text-neutral-500' : 'text-gray-500'}`}>
                Open the Google Maps link under any facility for turn-by-turn directions.
              </p>
            </div>
          </div>
        )}

        <div className="space-y-2">
          {facilities.map((facility, index) => (
            <FacilityCard
              key={index}
              facility={facility}
              index={index + 1}
              onSelect={hasCoords ? () => setSelectedFacility(facility) : undefined}
              selected={selectedFacility?.name === facility.name}
            />
          ))}
        </div>
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