import { useEffect, useRef, useState, useCallback } from 'react'
import { Map, Marker, Popup, NavigationControl, LngLatBounds, type GeoJSONSource } from 'maplibre-gl'
import 'maplibre-gl/dist/maplibre-gl.css'
import type { Facility } from '../types'

interface HospitalMapProps {
  facilities: Facility[]
  userLat?: number
  userLng?: number
  selectedFacility?: Facility | null
  onFacilitySelect?: (facility: Facility | null) => void
  dark?: boolean
}

const STYLE_URL = 'https://tiles.openfreemap.org/styles/liberty'
const OSRM_URL = 'https://router.project-osrm.org/route/v1/driving'

interface RouteInfo {
  distanceKm: number
  durationMin: number
}

function specialtyColor(specialty?: string): string {
  const s = (specialty || '').toLowerCase()
  if (s === 'emergency') return '#dc2626'
  if (s === 'pharmacy') return '#16a34a'
  if (s === 'diagnostic') return '#9333ea'
  return '#0891b2'
}

function buildPin(color: string, isSelected: boolean, isUser: boolean): HTMLDivElement {
  const el = document.createElement('div')
  el.className = 'relative'
  el.innerHTML = `
    <svg width="${isUser ? 26 : 30}" height="${isUser ? 26 : 38}" viewBox="0 0 24 36" fill="none" style="display:block">
      ${
        isUser
          ? '<circle cx="12" cy="12" r="10" fill="#2563eb" stroke="#fff" stroke-width="3"/>'
          : `<path d="M12 2C7 2 3 6 3 11c0 7 9 23 9 23s9-16 9-23c0-5-4-9-9-9z" fill="${color}" stroke="#fff" stroke-width="2"/>
             <rect x="9" y="9" width="6" height="6" rx="1.5" fill="#fff"/>
             <rect x="10.5" y="6.5" width="3" height="11" rx="1.5" fill="#fff" transform="rotate(0)"/>`
      }
    </svg>
  `
  if (isSelected) {
    el.style.transform = 'scale(1.25)'
    el.style.transition = 'transform 0.2s'
  }
  return el
}

export function HospitalMap({
  facilities,
  userLat,
  userLng,
  selectedFacility,
  onFacilitySelect,
  dark,
}: HospitalMapProps) {
  const containerRef = useRef<HTMLDivElement>(null)
  const mapRef = useRef<Map | null>(null)
  const markersRef = useRef<Record<string, Marker>>({})
  const [routeInfo, setRouteInfo] = useState<RouteInfo | null>(null)
  const [routeLoading, setRouteLoading] = useState(false)
  const [selected, setSelected] = useState<Facility | null>(null)

  const activeFacility = selectedFacility ?? selected

  const drawRoute = useCallback(
    async (facility: Facility) => {
      if (userLat === undefined || userLng === undefined || !facility.latitude || !facility.longitude) {
        setRouteInfo(null)
        return
      }
      const map = mapRef.current
      if (!map) return
      setRouteLoading(true)
      try {
        const url = `${OSRM_URL}/${userLng},${userLat};${facility.longitude},${facility.latitude}?overview=full&geometries=geojson`
        const resp = await fetch(url)
        if (!resp.ok) throw new Error('route failed')
        const data = await resp.json()
        const route = data?.routes?.[0]
        if (!route) throw new Error('no route')
        const coords = route.geometry?.coordinates
        if (!coords) throw new Error('no geometry')
        const source = map.getSource('route') as GeoJSONSource | undefined
        if (source) {
          source.setData({
            type: 'Feature',
            properties: {},
            geometry: { type: 'LineString', coordinates: coords },
          })
        }
        setRouteInfo({
          distanceKm: Math.round((route.distance || 0) / 100) / 10,
          durationMin: Math.round((route.duration || 0) / 60),
        })
        map.fitBounds(
          [
            [Math.min(userLng, facility.longitude), Math.min(userLat, facility.latitude)],
            [Math.max(userLng, facility.longitude), Math.max(userLat, facility.latitude)],
          ],
          { padding: 60, duration: 800 },
        )
      } catch {
        setRouteInfo(null)
      } finally {
        setRouteLoading(false)
      }
    },
    [userLat, userLng],
  )

  useEffect(() => {
    if (!containerRef.current || mapRef.current) return
    const map = new Map({
      container: containerRef.current,
      style: STYLE_URL,
      center: [userLng ?? 77.5946, userLat ?? 12.9716],
      zoom: 12,
      attributionControl: { compact: false },
    })
    mapRef.current = map

    map.addControl(new NavigationControl({ showCompass: false }), 'top-right')

    map.on('load', () => {
      map.addSource('route', {
        type: 'geojson',
        data: { type: 'Feature', properties: {}, geometry: { type: 'LineString', coordinates: [] } },
      })
      map.addLayer({
        id: 'route-line',
        type: 'line',
        source: 'route',
        layout: { 'line-cap': 'round', 'line-join': 'round' },
        paint: {
          'line-color': '#2563eb',
          'line-width': 5,
          'line-opacity': 0.85,
        },
      })
    })

    return () => {
      map.remove()
      mapRef.current = null
    }
  }, [userLat, userLng])

  useEffect(() => {
    const map = mapRef.current
    if (!map) return

    Object.values(markersRef.current).forEach((m) => m.remove())
    markersRef.current = {}

    if (userLat !== undefined && userLng !== undefined) {
      const userPin = buildPin('#2563eb', false, true)
      const userMarker = new Marker({ element: userPin })
        .setLngLat([userLng, userLat])
        .setPopup(new Popup({ offset: 12 }).setText('You are here'))
        .addTo(map)
      markersRef.current['user'] = userMarker
    }

    facilities.forEach((f, i) => {
      if (f.latitude === undefined || f.longitude === undefined) return
      const isSelected = activeFacility?.name === f.name
      const pin = buildPin(specialtyColor(f.specialty), isSelected, false)
      const marker = new Marker({ element: pin, anchor: 'bottom' })
        .setLngLat([f.longitude, f.latitude])
        .setPopup(new Popup({ offset: 22 }).setHTML(`<strong>${f.name}</strong><br/>${f.address || ''}`))
        .addTo(map)
      pin.addEventListener('click', () => {
        setSelected(f)
        onFacilitySelect?.(f)
        drawRoute(f)
      })
      markersRef.current[`facility-${i}`] = marker
    })

    if (facilities.length > 0 && (userLat === undefined || userLng === undefined)) {
      const bounds = new LngLatBounds()
      facilities.forEach((f) => {
        if (f.latitude !== undefined && f.longitude !== undefined) {
          bounds.extend([f.longitude, f.latitude])
        }
      })
      if (!bounds.isEmpty()) map.fitBounds(bounds, { padding: 60 })
    }
  }, [facilities, userLat, userLng, activeFacility, onFacilitySelect, drawRoute])

  useEffect(() => {
    if (activeFacility) drawRoute(activeFacility)
  }, [activeFacility, drawRoute])

  return (
    <div className={`rounded-xl overflow-hidden border ${dark ? 'border-[#383838]' : 'border-gray-200'}`}>
      <div ref={containerRef} className="h-56 w-full" />
      {routeLoading && (
        <div className="px-3 py-1.5 text-xs text-gray-500 dark:text-neutral-400">Calculating route…</div>
      )}
      {routeInfo && !routeLoading && (
        <div className="px-3 py-2 text-xs flex items-center gap-2 border-t border-gray-200 dark:border-[#383838] bg-gray-50 dark:bg-[#1e1e1e] text-gray-700 dark:text-neutral-300">
          <svg className="w-3.5 h-3.5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
          </svg>
          <span>~{routeInfo.distanceKm} km · ~{routeInfo.durationMin} min by road to {activeFacility?.name}</span>
        </div>
      )}
    </div>
  )
}