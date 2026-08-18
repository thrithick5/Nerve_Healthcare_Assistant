import httpx
from bs4 import BeautifulSoup
from urllib.parse import quote_plus
from typing import Optional
import re
import json


SPECIALTY_MAPPING = {
    "emergency": {
        "keywords": ["chest pain", "severe trauma", "stroke", "heart attack", "breathing difficulty",
                      "unconscious", "severe bleeding", "accident", "emergency", "critical",
                      "paralysis", "seizure", "choking", "anaphylaxis", "severe burn"],
        "facility_types": ["Emergency Room", "24/7 Hospital", "Trauma Center"],
        "search_queries": ["emergency hospital", "24/7 emergency care hospital", "emergency room near me"],
    },
    "cardiology": {
        "keywords": ["heart", "cardiac", "chest pain", "blood pressure", "hypertension",
                      "arrhythmia", "palpitation", "cardiologist"],
        "facility_types": ["Cardiology Hospital", "Heart Clinic", "Cardiac Center"],
        "search_queries": ["cardiology hospital", "heart specialist hospital", "cardiac care center"],
    },
    "orthopedics": {
        "keywords": ["bone", "joint", "fracture", "knee", "hip", "spine", "back pain",
                      "orthopedic", "arthritis", "sprain", "dislocation"],
        "facility_types": ["Orthopedic Clinic", "Orthopedic Hospital", "Bone & Joint Center"],
        "search_queries": ["orthopedic hospital", "bone specialist hospital", "joint clinic"],
    },
    "neurology": {
        "keywords": ["brain", "neurology", "headache", "migraine", "epilepsy", "stroke",
                      "nerve", "neurologist", "paralysis", "parkinson", "alzheimer"],
        "facility_types": ["Neurology Hospital", "Neuro Clinic", "Brain & Spine Center"],
        "search_queries": ["neurology hospital", "brain specialist hospital", "neuro clinic"],
    },
    "pediatrics": {
        "keywords": ["child", "baby", "infant", "pediatric", "kids", "children",
                      "vaccination", "child fever", "growth"],
        "facility_types": ["Pediatric Hospital", "Children's Hospital", "Child Care Clinic"],
        "search_queries": ["pediatric hospital", "children hospital", "child specialist hospital"],
    },
    "dermatology": {
        "keywords": ["skin", "rash", "acne", "eczema", "psoriasis", "dermatologist",
                      "allergy skin", "hair loss", "pigmentation"],
        "facility_types": ["Dermatology Clinic", "Skin Care Center", "Skin Hospital"],
        "search_queries": ["dermatology clinic", "skin specialist hospital", "skin care center"],
    },
    "ophthalmology": {
        "keywords": ["eye", "vision", "glasses", "cataract", "glaucoma", "retina",
                      "ophthalmologist", "eye checkup"],
        "facility_types": ["Eye Hospital", "Ophthalmology Clinic", "Eye Care Center"],
        "search_queries": ["eye hospital", "ophthalmology clinic", "eye care center"],
    },
    "oncology": {
        "keywords": ["cancer", "tumor", "oncology", "chemotherapy", "radiation",
                      "oncologist", "malignant"],
        "facility_types": ["Cancer Hospital", "Oncology Center", "Tumor Clinic"],
        "search_queries": ["cancer hospital", "oncology center", "tumor treatment hospital"],
    },
    "gynecology": {
        "keywords": ["pregnancy", "gynecologist", "women health", "menstrual", "妇科",
                      "maternity", "obstetric", "fertility", "IVF"],
        "facility_types": ["Gynecology Hospital", "Maternity Hospital", "Women's Health Center"],
        "search_queries": ["gynecology hospital", "maternity hospital", "women health center"],
    },
    "dentistry": {
        "keywords": ["tooth", "dental", "teeth", "braces", "root canal", "dentist",
                      "gum", "oral", "wisdom tooth"],
        "facility_types": ["Dental Hospital", "Dental Clinic", "Oral Care Center"],
        "search_queries": ["dental hospital", "dentist clinic", "oral care center"],
    },
    "ent": {
        "keywords": ["ear", "nose", "throat", "ENT", "hearing", "sinus", "tonsil",
                      "voice", "nasal"],
        "facility_types": ["ENT Hospital", "ENT Clinic", "Ear Nose Throat Center"],
        "search_queries": ["ENT hospital", "ear nose throat clinic", "ENT specialist"],
    },
    "pulmonology": {
        "keywords": ["lung", "breathing", "asthma", "respiratory", "pulmonary",
                      "pneumonia", "bronchitis", "copd", "cough"],
        "facility_types": ["Pulmonology Hospital", "Lung Clinic", "Respiratory Center"],
        "search_queries": ["pulmonology hospital", "lung specialist hospital", "respiratory clinic"],
    },
    "gastroenterology": {
        "keywords": ["stomach", "digestive", "liver", "gastro", "colonoscopy",
                      "gastric", "ulcer", "IBS", "constipation"],
        "facility_types": ["Gastroenterology Hospital", "Digestive Care Center", "Liver Clinic"],
        "search_queries": ["gastroenterology hospital", "liver specialist hospital", "digestive care center"],
    },
    "urology": {
        "keywords": ["kidney", "urinary", "bladder", "prostate", "urologist",
                      "stone", "dialysis"],
        "facility_types": ["Urology Hospital", "Kidney Hospital", "Urology Clinic"],
        "search_queries": ["urology hospital", "kidney specialist hospital", "urology clinic"],
    },
    "psychiatry": {
        "keywords": ["mental health", "depression", "anxiety", "psychiatrist",
                      "psychology", "stress", "bipolar", "OCD", "insomnia"],
        "facility_types": ["Psychiatric Hospital", "Mental Health Center", "Psychiatry Clinic"],
        "search_queries": ["psychiatric hospital", "mental health center", "psychiatrist near me"],
    },
    "pharmacy": {
        "keywords": ["medicine", "medication", "drug", "pharmacy", "medical store",
                      "chemist", "prescription"],
        "facility_types": ["24/7 Pharmacy", "Medical Store", "Pharmacy"],
        "search_queries": ["24/7 pharmacy near me", "medical store near me", "pharmacy open now"],
    },
    "diagnostic": {
        "keywords": ["lab test", "blood test", "X-ray", "MRI", "CT scan", "diagnostic",
                      "pathology", "checkup", "health check"],
        "facility_types": ["Diagnostic Lab", "Pathology Lab", "Imaging Center"],
        "search_queries": ["diagnostic lab near me", "pathology lab", "health checkup center"],
    },
    "general": {
        "keywords": ["doctor", "hospital", "clinic", "general physician", "checkup",
                      "consultation", "fever", "cold", "flu"],
        "facility_types": ["Multi-Specialty Hospital", "General Hospital", "Polyclinic"],
        "search_queries": ["hospital near me", "general hospital", "polyclinic near me"],
    },
}


class FacilityFinderService:
    def __init__(self):
        self.client = httpx.Client(
            headers={
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                              "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
            },
            timeout=15,
            follow_redirects=True,
        )

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
        }

    def generate_maps_search_url(
        self, query: str, location: str,
        latitude: float | None = None, longitude: float | None = None,
    ) -> str:
        if latitude is not None and longitude is not None:
            # Anchor the search to exact GPS coordinates
            encoded = quote_plus(query)
            return (
                f"https://www.google.com/maps/search/{encoded}/@{latitude},{longitude},13z"
            )
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

    def scrape_google_facilities(self, query: str, location: str) -> list[dict]:
        try:
            search_query = f"{query} {location}"
            url = f"https://www.google.com/search?q={quote_plus(search_query)}&hl=en"
            resp = self.client.get(url)
            if resp.status_code != 200:
                return []
            soup = BeautifulSoup(resp.text, "html.parser")
            facilities = []
            for result in soup.select("div[data-attrid]")[:10]:
                name_el = result.select_one("h3, span[class]")
                if not name_el:
                    continue
                name = name_el.get_text(strip=True)
                if not name or len(name) < 3:
                    continue
                rating = None
                review_count = None
                rating_text = result.get_text()
                rating_match = re.search(r"(\d+\.?\d*)\s*\(", rating_text)
                if rating_match:
                    rating = float(rating_match.group(1))
                    review_match = re.search(r"\((\d[\d,]*)\)", rating_text)
                    if review_match:
                        review_count = int(review_match.group(1).replace(",", ""))
                address = ""
                for span in result.select("span"):
                    text = span.get_text(strip=True)
                    if any(w in text.lower() for w in ["road", "street", "lane", "nagar", "road", "area", "city", "district"]):
                        address = text
                        break
                maps_url = self.generate_maps_directions_url(name, location)
                facilities.append({
                    "name": name,
                    "rating": rating,
                    "review_count": review_count,
                    "address": address,
                    "maps_url": maps_url,
                    "source": "google_search",
                })
            return facilities
        except Exception:
            return []

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

    def find_facilities(
        self, health_issue: str, location: str,
        latitude: float | None = None, longitude: float | None = None,
    ) -> dict:
        specialty_info = self.map_health_issue_to_specialty(health_issue)
        primary_query = specialty_info["search_queries"][0]
        scraped = self.scrape_google_facilities(primary_query, location)
        if scraped:
            scraped.sort(key=lambda f: (f.get("rating") or 0), reverse=True)
            top_facilities = scraped[:3]
            for f in top_facilities:
                if not f.get("maps_url"):
                    f["maps_url"] = self.generate_maps_directions_url(
                        f["name"], location, latitude, longitude
                    )
                f["specialty"] = specialty_info["specialty"]
            return {
                "specialty": specialty_info["specialty"],
                "facility_types": specialty_info["facility_types"],
                "search_url": self.generate_maps_search_url(
                    primary_query, location, latitude, longitude
                ),
                "facilities": top_facilities,
            }
        return self._build_curated_facilities(health_issue, location, latitude, longitude)

    def format_facilities_as_markdown(self, result: dict) -> str:
        specialty = result["specialty"].title()
        facilities = result["facilities"]
        search_url = result["search_url"]
        lines = [
            f"Based on your symptoms, I recommend looking for **{specialty}** facilities. ",
            "",
            f"Here are the top options for you:",
            "",
        ]
        for i, f in enumerate(facilities, 1):
            name = f.get("name", "Healthcare Facility")
            rating = f.get("rating")
            reviews = f.get("review_count")
            address = f.get("address", "")
            maps_url = f.get("maps_url", "")
            lines.append(f"**{i}. {name}**")
            if rating:
                stars = "★" * int(rating) + "☆" * (5 - int(rating))
                review_str = f" ({reviews} reviews)" if reviews else ""
                lines.append(f"   - **Google Rating:** {stars} {rating}{review_str}")
            if address:
                lines.append(f"   - **Address:** {address}")
            lines.append(f"   - [Open in Google Maps]({maps_url})")
            lines.append("")
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
