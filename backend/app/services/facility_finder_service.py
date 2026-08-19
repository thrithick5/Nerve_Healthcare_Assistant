from __future__ import annotations
import httpx
from bs4 import BeautifulSoup
from urllib.parse import quote_plus
from typing import Optional, List, Dict, Any
import re
import math
import time
import threading
from concurrent.futures import ThreadPoolExecutor


SPECIALTY_MAPPING = {
    "emergency": {
        "keywords": ["chest pain", "severe trauma", "stroke", "heart attack", "breathing difficulty",
                      "unconscious", "severe bleeding", "accident", "emergency", "critical",
                      "paralysis", "seizure", "choking", "anaphylaxis", "severe burn"],
        "facility_types": ["Emergency Room", "24/7 Hospital", "Trauma Center"],
        "search_queries": ["emergency hospital", "24/7 emergency care hospital", "emergency room near me"],
        "amenities": ["hospital"],
    },
    "cardiology": {
        "keywords": ["heart", "cardiac", "chest pain", "blood pressure", "hypertension",
                      "arrhythmia", "palpitation", "cardiologist"],
        "facility_types": ["Cardiology Hospital", "Heart Clinic", "Cardiac Center"],
        "search_queries": ["cardiology hospital", "heart specialist hospital", "cardiac care center"],
        "amenities": ["hospital", "clinic"],
    },
    "orthopedics": {
        "keywords": ["bone", "joint", "fracture", "knee", "hip", "spine", "back pain",
                      "orthopedic", "ortho", "arthritis", "sprain", "dislocation"],
        "facility_types": ["Orthopedic Clinic", "Orthopedic Hospital", "Bone & Joint Center"],
        "search_queries": ["orthopedic hospital", "bone specialist hospital", "joint clinic"],
        "amenities": ["hospital", "clinic"],
    },
    "neurology": {
        "keywords": ["brain", "neurology", "headache", "migraine", "epilepsy", "stroke",
                      "nerve", "neurologist", "paralysis", "parkinson", "alzheimer"],
        "facility_types": ["Neurology Hospital", "Neuro Clinic", "Brain & Spine Center"],
        "search_queries": ["neurology hospital", "brain specialist hospital", "neuro clinic"],
        "amenities": ["hospital", "clinic"],
    },
    "pediatrics": {
        "keywords": ["child", "baby", "infant", "pediatric", "kids", "children",
                      "vaccination", "child fever", "growth"],
        "facility_types": ["Pediatric Hospital", "Children's Hospital", "Child Care Clinic"],
        "search_queries": ["pediatric hospital", "children hospital", "child specialist hospital"],
        "amenities": ["hospital", "clinic"],
    },
    "dermatology": {
        "keywords": ["skin", "rash", "acne", "eczema", "psoriasis", "dermatologist",
                      "allergy skin", "hair loss", "pigmentation"],
        "facility_types": ["Dermatology Clinic", "Skin Care Center", "Skin Hospital"],
        "search_queries": ["dermatology clinic", "skin specialist hospital", "skin care center"],
        "amenities": ["clinic", "hospital"],
    },
    "ophthalmology": {
        "keywords": ["eye", "vision", "glasses", "cataract", "glaucoma", "retina",
                      "ophthalmologist", "eye checkup"],
        "facility_types": ["Eye Hospital", "Ophthalmology Clinic", "Eye Care Center"],
        "search_queries": ["eye hospital", "ophthalmology clinic", "eye care center"],
        "amenities": ["hospital", "clinic"],
    },
    "oncology": {
        "keywords": ["cancer", "tumor", "oncology", "chemotherapy", "radiation",
                      "oncologist", "malignant"],
        "facility_types": ["Cancer Hospital", "Oncology Center", "Tumor Clinic"],
        "search_queries": ["cancer hospital", "oncology center", "tumor treatment hospital"],
        "amenities": ["hospital", "clinic"],
    },
    "gynecology": {
        "keywords": ["pregnancy", "gynecologist", "women health", "menstrual",
                      "maternity", "obstetric", "fertility", "ivf", "womens"],
        "facility_types": ["Gynecology Hospital", "Maternity Hospital", "Women's Health Center"],
        "search_queries": ["gynecology hospital", "maternity hospital", "women health center"],
        "amenities": ["hospital", "clinic"],
    },
    "dentistry": {
        "keywords": ["tooth", "dental", "teeth", "braces", "root canal", "dentist",
                      "gum", "oral", "wisdom tooth"],
        "facility_types": ["Dental Hospital", "Dental Clinic", "Oral Care Center"],
        "search_queries": ["dental hospital", "dentist clinic", "oral care center"],
        "amenities": ["clinic", "dentist"],
    },
    "ent": {
        "keywords": ["ear", "nose", "throat", "ent", "hearing", "sinus", "tonsil",
                      "voice", "nasal"],
        "facility_types": ["ENT Hospital", "ENT Clinic", "Ear Nose Throat Center"],
        "search_queries": ["ENT hospital", "ear nose throat clinic", "ENT specialist"],
        "amenities": ["hospital", "clinic"],
    },
    "pulmonology": {
        "keywords": ["lung", "breathing", "asthma", "respiratory", "pulmonary",
                      "pneumonia", "bronchitis", "copd", "cough"],
        "facility_types": ["Pulmonology Hospital", "Lung Clinic", "Respiratory Center"],
        "search_queries": ["pulmonology hospital", "lung specialist hospital", "respiratory clinic"],
        "amenities": ["hospital", "clinic"],
    },
    "gastroenterology": {
        "keywords": ["stomach", "digestive", "liver", "gastro", "colonoscopy",
                      "gastric", "ulcer", "ibs", "constipation"],
        "facility_types": ["Gastroenterology Hospital", "Digestive Care Center", "Liver Clinic"],
        "search_queries": ["gastroenterology hospital", "liver specialist hospital", "digestive care center"],
        "amenities": ["hospital", "clinic"],
    },
    "urology": {
        "keywords": ["kidney", "urinary", "bladder", "prostate", "urologist",
                      "stone", "dialysis"],
        "facility_types": ["Urology Hospital", "Kidney Hospital", "Urology Clinic"],
        "search_queries": ["urology hospital", "kidney specialist hospital", "urology clinic"],
        "amenities": ["hospital", "clinic"],
    },
    "psychiatry": {
        "keywords": ["mental health", "depression", "anxiety", "psychiatrist",
                      "psychology", "stress", "bipolar", "ocd", "insomnia"],
        "facility_types": ["Psychiatric Hospital", "Mental Health Center", "Psychiatry Clinic"],
        "search_queries": ["psychiatric hospital", "mental health center", "psychiatrist near me"],
        "amenities": ["hospital", "clinic"],
    },
    "pharmacy": {
        "keywords": ["medicine", "medication", "drug", "pharmacy", "medical store",
                      "chemist", "prescription"],
        "facility_types": ["24/7 Pharmacy", "Medical Store", "Pharmacy"],
        "search_queries": ["24/7 pharmacy near me", "medical store near me", "pharmacy open now"],
        "amenities": ["pharmacy"],
    },
    "diagnostic": {
        "keywords": ["lab test", "blood test", "x-ray", "mri", "ct scan", "diagnostic",
                      "pathology", "checkup", "health check"],
        "facility_types": ["Diagnostic Lab", "Pathology Lab", "Imaging Center"],
        "search_queries": ["diagnostic lab near me", "pathology lab", "health checkup center"],
        "amenities": ["clinic", "hospital"],
    },
    "general": {
        "keywords": ["doctor", "hospital", "clinic", "general physician", "checkup",
                      "consultation", "fever", "cold", "flu", "nearest"],
        "facility_types": ["Multi-Specialty Hospital", "General Hospital", "Polyclinic"],
        "search_queries": ["hospital near me", "general hospital", "polyclinic near me"],
        "amenities": ["hospital", "clinic"],
    },
}

# Emergency helplines per region (shown for red-flag symptoms)
EMERGENCY_QUERY = ["chest pain", "stroke", "heart attack", "severe trauma", "breathing difficulty",
                   "unconscious", "severe bleeding", "accident", "seizure", "choking",
                   "anaphylaxis", "severe burn", "paralysis"]

OVER_PASS_ENDPOINTS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
]

NOMINATIM_ENDPOINT = "https://nominatim.openstreetmap.org/search"


class FacilityFinderService:
    def __init__(self):
        self.client = httpx.Client(
            headers={
                "User-Agent": "NerveHealthcareAssistant/2.0 (healthcare navigation helper)",
                "Accept": "application/json, text/html",
                "Accept-Language": "en-US,en;q=0.5",
            },
            timeout=15,
            follow_redirects=True,
        )
        self._cache: dict[str, tuple[float, list[dict]]] = {}
        self._cache_lock = threading.Lock()
        self._last_request_time: dict[str, float] = {}

    # ─── Specialty mapping ────────────────────────────────────────────────
    def map_health_issue_to_specialty(self, health_issue: str) -> dict:
        issue_lower = health_issue.lower()
        best_match = None
        best_score = 0
        for specialty, config in SPECIALTY_MAPPING.items():
            score = sum(1 for kw in config["keywords"] if kw in issue_lower)
            if score > best_score:
                best_score = score
                best_match = specialty
        if not best_match:
            best_match = "general"
        return {
            "specialty": best_match,
            "facility_types": SPECIALTY_MAPPING[best_match]["facility_types"],
            "search_queries": SPECIALTY_MAPPING[best_match]["search_queries"],
            "amenities": SPECIALTY_MAPPING[best_match]["amenities"],
            "keywords": SPECIALTY_MAPPING[best_match]["keywords"],
        }

    def is_emergency(self, health_issue: str) -> bool:
        issue_lower = health_issue.lower()
        return any(kw in issue_lower for kw in EMERGENCY_QUERY)

    # ─── Geocoding (Nominatim, free OSM) ──────────────────────────────────
    def geocode_location(self, location: str) -> Optional[tuple[float, float]]:
        if not location:
            return None
        try:
            resp = self.client.get(
                NOMINATIM_ENDPOINT,
                params={"q": location, "format": "json", "limit": 1},
            )
            if resp.status_code != 200:
                return None
            data = resp.json()
            if data and "lat" in data[0]:
                return float(data[0]["lat"]), float(data[0]["lon"])
        except Exception:
            pass
        return None

    # ─── Real facility search via Overpass (free OSM data) ────────────────
    def _overpass_query(self, lat: float, lng: float, amenities: list[str], radius: int = 20000) -> list[dict]:
        cache_key = f"{round(lat, 3)},{round(lng, 3)}|{','.join(sorted(amenities))}"
        now = time.time()
        with self._cache_lock:
            if cache_key in self._cache:
                cached_at, cached = self._cache[cache_key]
                if now - cached_at < 900:
                    return cached

        amenity_filter = "".join(
            f'  nwr["amenity"="{a}"](around:{radius},{lat},{lng});\n' for a in amenities
        )
        query = f"""
[out:json][timeout:25];
(
{amenity_filter}
);
out center tags 50;
"""

        # Respect a ~1s gap between hits to the public Overpass endpoints (rate-limited)
        with self._cache_lock:
            last = self._last_request_time.get("overpass", 0)
            wait = max(0.0, last + 1.5 - now)
        if wait > 0:
            time.sleep(wait)

        result: list[dict] = []
        for endpoint in OVER_PASS_ENDPOINTS:
            try:
                resp = self.client.post(endpoint, content=query.encode(), timeout=30)
                with self._cache_lock:
                    self._last_request_time["overpass"] = time.time()
                if resp.status_code != 200:
                    time.sleep(1.0)
                    continue
                data = resp.json()
                elements = data.get("elements", [])
                result = self._normalize_overpass_elements(elements, lat, lng)
                if result:
                    break
                time.sleep(1.0)
            except Exception:
                time.sleep(1.0)
                continue

        with self._cache_lock:
            self._cache[cache_key] = (time.time(), result)
        return result

    def _normalize_overpass_elements(self, elements: list[dict], lat: float, lng: float) -> list[dict]:
        facilities = []
        for el in elements:
            tags = el.get("tags", {})
            name = tags.get("name", "").strip()
            if not name:
                continue
            if tags.get("amenity") in ("community_centre", "place_of_worship"):
                continue
            if el.get("type") == "node":
                el_lat = el.get("lat")
                el_lng = el.get("lon")
            else:
                center = el.get("center", {})
                el_lat = center.get("lat")
                el_lng = center.get("lon")
            if el_lat is None or el_lng is None:
                continue
            address_parts = [
                tags.get("addr:housenumber", ""),
                tags.get("addr:street", ""),
                tags.get("addr:city", ""),
                tags.get("addr:postcode", ""),
            ]
            address = ", ".join(p for p in address_parts if p)
            facilities.append({
                "name": name,
                "latitude": float(el_lat),
                "longitude": float(el_lng),
                "address": address,
                "phone": tags.get("phone", ""),
                "opening_hours": tags.get("opening_hours", ""),
                "emergency": tags.get("emergency", "") == "yes",
                "amenity": tags.get("amenity", ""),
                "distance_km": self._haversine_km(lat, lng, float(el_lat), float(el_lng)),
            })
        return facilities

    @staticmethod
    def _haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
        r = 6371.0
        dlat = math.radians(lat2 - lat1)
        dlng = math.radians(lng2 - lng1)
        a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlng / 2) ** 2
        return round(r * 2 * math.asin(math.sqrt(a)), 1)

    def _specialty_score(self, name: str, specialty_config: dict) -> int:
        name_lower = name.lower()
        return sum(1 for kw in specialty_config["keywords"] if kw in name_lower)

    # ─── Google Maps URL helpers (external fallback, no SDK) ──────────────
    def generate_maps_search_url(
        self, query: str, location: str,
        latitude: float | None = None, longitude: float | None = None,
    ) -> str:
        if latitude is not None and longitude is not None:
            encoded = quote_plus(query)
            return f"https://www.google.com/maps/search/{encoded}/@{latitude},{longitude},13z"
        search_term = f"{query} {location}".strip()
        encoded = quote_plus(search_term)
        return f"https://www.google.com/maps/search/?api=1&query={encoded}"

    def generate_maps_directions_url(
        self, destination: str, location: str,
        latitude: float | None = None, longitude: float | None = None,
    ) -> str:
        dest_term = f"{destination} {location}".strip()
        encoded = quote_plus(dest_term)
        if latitude is not None and longitude is not None:
            origin = f"{latitude},{longitude}"
            return f"https://www.google.com/maps/dir/?api=1&origin={origin}&destination={encoded}"
        return f"https://www.google.com/maps/dir/?api=1&destination={encoded}"

    # ─── Rating enrichment (best-effort, short timeout) ───────────────────
    def _enrich_rating(self, facility: dict) -> dict:
        """Try to fetch a Google rating for a facility. Never blocks the main flow for long."""
        try:
            name = facility.get("name", "")
            query = f"{name} hospital"
            url = f"https://www.google.com/search?q={quote_plus(query)}&hl=en"
            resp = self.client.get(url, timeout=6)
            if resp.status_code != 200:
                return facility
            soup = BeautifulSoup(resp.text, "html.parser")
            page_text = soup.get_text(" ", strip=True)
            rating_match = re.search(r"(\d+\.\d+)\s*\(([\d,]+)\s*reviews?\)", page_text)
            if rating_match:
                facility["rating"] = float(rating_match.group(1))
                facility["review_count"] = int(rating_match.group(2).replace(",", ""))
        except Exception:
            pass
        return facility

    # ─── Main search ──────────────────────────────────────────────────────
    def find_facilities(
        self, health_issue: str, location: str,
        latitude: float | None = None, longitude: float | None = None,
        include_ratings: bool = False,
    ) -> dict:
        specialty_info = self.map_health_issue_to_specialty(health_issue)
        coords = None
        if latitude is not None and longitude is not None:
            coords = (float(latitude), float(longitude))
        elif location:
            coords = self.geocode_location(location)
        if coords is None:
            return self._build_curated_facilities(
                health_issue, location, latitude, longitude
            )

        lat, lng = coords
        radius = 25000 if self.is_emergency(health_issue) else 20000
        facilities = self._overpass_query(lat, lng, specialty_info["amenities"], radius)

        if facilities:
            for f in facilities:
                f["specialty"] = specialty_info["specialty"]
                f["score"] = self._specialty_score(f["name"], specialty_info)
            facilities.sort(key=lambda f: (-f["score"], f["distance_km"]))
            top = facilities[:3]
            if include_ratings:
                with ThreadPoolExecutor(max_workers=3) as pool:
                    top = list(pool.map(self._enrich_rating, top))
            for f in top:
                f["maps_url"] = self.generate_maps_directions_url(
                    f["name"], location, f["latitude"], f["longitude"]
                )
            return {
                "specialty": specialty_info["specialty"],
                "facility_types": specialty_info["facility_types"],
                "search_url": self.generate_maps_search_url(
                    specialty_info["search_queries"][0], location, lat, lng
                ),
                "facilities": top,
                "latitude": lat,
                "longitude": lng,
                "resolved_location": True,
            }

        return self._build_curated_facilities(health_issue, location, lat, lng)

    def _build_curated_facilities(
        self, health_issue: str, location: str,
        latitude: float | None = None, longitude: float | None = None,
    ) -> dict:
        specialty_info = self.map_health_issue_to_specialty(health_issue)
        primary_query = specialty_info["search_queries"][0]
        search_url = self.generate_maps_search_url(primary_query, location, latitude, longitude)
        facilities = []
        for ft in specialty_info["facility_types"][:3]:
            maps_search = self.generate_maps_search_url(f"{ft}", location, latitude, longitude)
            facilities.append({
                "name": f"Search: {ft}{' in ' + location if location and location != 'nearby' else ' near you'}",
                "rating": None,
                "review_count": None,
                "address": "",
                "maps_url": maps_search,
                "source": "curated_search",
                "facility_type": ft,
                "specialty": specialty_info["specialty"],
            })
        return {
            "specialty": specialty_info["specialty"],
            "facility_types": specialty_info["facility_types"],
            "search_url": search_url,
            "facilities": facilities,
        }

    # ─── Markdown formatter ───────────────────────────────────────────────
    def format_facilities_as_markdown(self, result: dict) -> str:
        specialty = result["specialty"].title()
        facilities = result.get("facilities", [])
        search_url = result.get("search_url", "")
        lines = [
            f"Based on your symptoms, I recommend looking for **{specialty}** facilities. ",
            "",
            "Here are the top options near you:",
            "",
        ]
        for i, f in enumerate(facilities, 1):
            name = f.get("name", "Healthcare Facility")
            rating = f.get("rating")
            reviews = f.get("review_count")
            address = f.get("address", "")
            distance = f.get("distance_km")
            maps_url = f.get("maps_url", "")
            lines.append(f"**{i}. {name}**")
            if rating:
                stars = "★" * int(rating) + "☆" * (5 - int(rating))
                review_str = f" ({reviews} reviews)" if reviews else ""
                lines.append(f"   - **Google Rating:** {stars} {rating}{review_str}")
            if distance:
                lines.append(f"   - **Distance:** ~{distance} km away")
            if address:
                lines.append(f"   - **Address:** {address}")
            lines.append(f"   - [Open in Google Maps]({maps_url})")
            lines.append("")
        if search_url:
            lines.append(f"[Search all {specialty} facilities on Google Maps]({search_url})")
            lines.append("")
        lines.append("**Safety Notice:** If you are experiencing a life-threatening emergency, please call your local emergency number (112 / 108 / 911) or visit the nearest Emergency Room immediately.")
        return "\n".join(lines)

    def close(self):
        self.client.close()

    def __del__(self):
        try:
            self.close()
        except Exception:
            pass