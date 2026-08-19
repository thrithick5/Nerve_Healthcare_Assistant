import type { Facility } from '../types'

interface FacilityCardProps {
  facility: Facility
  index: number
  onSelect?: (facility: Facility) => void
  selected?: boolean
}

export function FacilityCard({ facility, index, onSelect, selected }: FacilityCardProps) {
  const { name, rating, review_count, address, maps_url, facility_type, distance_km, phone, opening_hours, emergency } = facility

  const renderStars = (rating: number) => {
    const full = Math.floor(rating)
    const hasHalf = rating - full >= 0.5
    const empty = 5 - full - (hasHalf ? 1 : 0)
    return (
      <span className="inline-flex items-center gap-0.5">
        {Array.from({ length: full }).map((_, i) => (
          <span key={`f-${i}`} className="text-amber-400 text-sm">★</span>
        ))}
        {hasHalf && <span className="text-amber-400 text-sm">★</span>}
        {Array.from({ length: empty }).map((_, i) => (
          <span key={`e-${i}`} className="text-gray-300 dark:text-gray-600 text-sm">☆</span>
        ))}
      </span>
    )
  }

  return (
    <div
      onClick={onSelect ? () => onSelect(facility) : undefined}
      className={`border rounded-xl p-4 transition-colors bg-white dark:bg-[#1e1e1e] ${
        selected
          ? 'border-primary-400 dark:border-primary-600 ring-2 ring-primary-200 dark:ring-primary-800'
          : 'border-gray-200 dark:border-[#383838] hover:border-primary-300 dark:hover:border-primary-700'
      } ${onSelect ? 'cursor-pointer' : ''}`}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <span className="text-xs font-bold text-primary-600 dark:text-primary-400 bg-primary-50 dark:bg-primary-900/20 rounded-full w-6 h-6 flex items-center justify-center shrink-0">
              {index}
            </span>
            <h4 className="font-semibold text-sm text-gray-900 dark:text-white truncate">
              {name}
            </h4>
            {emergency && (
              <span className="shrink-0 text-[10px] font-semibold uppercase tracking-wide text-white bg-red-600 rounded-full px-2 py-0.5">
                24/7 ER
              </span>
            )}
          </div>
          {(facility_type || distance_km) && (
            <div className="flex items-center gap-2 ml-8 flex-wrap">
              {facility_type && (
                <span className="text-xs text-gray-500 dark:text-gray-400">{facility_type}</span>
              )}
              {distance_km !== undefined && (
                <span className="text-xs font-medium text-gray-600 dark:text-gray-300">
                  ~{distance_km} km away
                </span>
              )}
            </div>
          )}
          {rating && (
            <div className="flex items-center gap-2 ml-8 mt-1">
              {renderStars(rating)}
              <span className="text-sm font-medium text-gray-700 dark:text-gray-300">{rating}</span>
              {review_count && (
                <span className="text-xs text-gray-500 dark:text-gray-400">({review_count.toLocaleString()} reviews)</span>
              )}
            </div>
          )}
          {address && (
            <p className="text-xs text-gray-500 dark:text-gray-400 ml-8 mt-1 flex items-center gap-1">
              <svg className="w-3 h-3 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
              </svg>
              {address}
            </p>
          )}
          {(phone || opening_hours) && (
            <div className="ml-8 mt-1 flex flex-wrap gap-2 text-xs text-gray-500 dark:text-gray-400">
              {phone && (
                <span className="flex items-center gap-1">
                  <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z" />
                  </svg>
                  {phone}
                </span>
              )}
              {opening_hours && <span>{opening_hours}</span>}
            </div>
          )}
        </div>
        <a
          href={maps_url}
          target="_blank"
          rel="noopener noreferrer"
          onClick={(e) => e.stopPropagation()}
          className="shrink-0 inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-white bg-primary-600 hover:bg-primary-700 rounded-lg transition-colors"
        >
          <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l4.553 2.276A1 1 0 0021 18.382V7.618a1 1 0 00-.553-.894L15 4m0 13V4m0 0L9 7" />
          </svg>
          Maps
        </a>
      </div>
    </div>
  )
}