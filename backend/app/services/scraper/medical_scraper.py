import httpx
from bs4 import BeautifulSoup
from typing import Optional
import re


class MedicalScraper:
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en-US,en;q=0.5",
        "Origin": "https://www.1mg.com",
        "Referer": "https://www.1mg.com/",
    }

    def __init__(self):
        self.client = httpx.Client(headers=self.HEADERS, timeout=30, follow_redirects=True)

    def search_1mg(self, query: str) -> Optional[list[dict]]:
        try:
            url = f"https://www.1mg.com/api/v1/search/suggestions?name={query.replace(' ', '+')}"
            resp = self.client.get(url, headers={**self.HEADERS, "Accept": "application/json"})
            if resp.status_code != 200:
                return None

            data = resp.json()
            results = data.get("results", [])
            drugs = []
            for r in results:
                url_path = r.get("url_path", "")
                raw = r.get("label") or r.get("name", "")
                clean_label = re.sub(r"<[^>]+>", "", raw).strip()
                if not url_path or not clean_label:
                    continue
                full_url = f"https://www.1mg.com{url_path}" if url_path.startswith("/") else url_path
                if "/generics/" in url_path:
                    drugs.append({"name": clean_label, "url": full_url})

            seen = set()
            unique = []
            for d in drugs:
                key = d["name"].lower().split(" in ")[0].split(" (")[0].strip()
                if key not in seen:
                    seen.add(key)
                    unique.append(d)
            return unique[:3] if unique else None
        except Exception:
            return None

    def get_drug_details(self, drug_url: str) -> Optional[dict]:
        try:
            resp = self.client.get(drug_url, headers={**self.HEADERS, "Accept": "text/html"})
            if resp.status_code != 200:
                return None

            soup = BeautifulSoup(resp.text, "html.parser")

            h1 = soup.find("h1")
            drug_name = h1.get_text(strip=True) if h1 else ""

            sections = {}
            heading_map = {
                "about": "about",
                "information about": "about",
                "use": "uses",
                "how it work": "how_it_works",
                "side effect": "side_effects",
                "common side effect": "side_effects",
                "expert advice": "expert_advice",
                "safety": "safety_advice",
                "warning": "safety_advice",
                "precaution": "safety_advice",
            }

            for section_div in soup.find_all("div", class_="pTop-16"):
                heading = section_div.find(["h2", "h3", "h4"])
                if not heading:
                    continue
                heading_text = heading.get_text(strip=True).lower()

                key = None
                for kw, mapped in heading_map.items():
                    if kw in heading_text:
                        key = mapped
                        break
                if not key:
                    continue

                content_divs = section_div.find_all("div", class_=lambda c: c and "bodyRegular" in c)
                texts = []
                for cd in content_divs:
                    t = cd.get_text(" ", strip=True)
                    if len(t) > 10:
                        texts.append(t)

                if texts:
                    if key not in sections:
                        sections[key] = []
                    sections[key].extend(texts)

            if not any(v for v in sections.values()):
                return None

            result = {"name": drug_name}
            for key, values in sections.items():
                result[key] = values
            return result
        except Exception:
            return None

    def scrape_medical_info(self, query: str) -> str:
        all_info = []
        drug_name = self._extract_drug_name(query)
        search_results = self.search_1mg(drug_name)
        if search_results:
            for result in search_results[:2]:
                details = self.get_drug_details(result["url"])
                if details:
                    drug_url = result.get("url", "")
                    lines = [f"Source: 1mg | Drug: {details.get('name', result['name'])}"]
                    if drug_url:
                        lines.append(f"URL: {drug_url}")
                    if details.get("about"):
                        lines.append("Information: " + details["about"][0])
                    if details.get("uses"):
                        lines.append("\nUses:\n" + "\n".join(f"- {u}" for u in details["uses"]))
                    if details.get("side_effects"):
                        lines.append("\nSide Effects:\n" + "\n".join(f"- {s}" for s in details["side_effects"]))
                    if details.get("expert_advice"):
                        lines.append("\nExpert Advice:\n" + "\n".join(f"- {a}" for a in details["expert_advice"]))

                    # Build text and sanitize common divider lines (e.g., --- or ***)
                    details_text = "\n".join(lines)
                    # Remove lines that are only made of '-', '*', or '_' (3 or more)
                    details_text = re.sub(r"(?m)^[\s]*[-*_]{3,}[\s]*$", "", details_text)
                    # Collapse excessive blank lines
                    details_text = re.sub(r"\n{3,}", "\n\n", details_text)
                    all_info.append(details_text)
        return "\n\n".join(all_info) if all_info else f"No drug information found for: {query}"

    def _extract_drug_name(self, query: str) -> str:
        q = query.strip().lower()
        stop_words = {"what", "is", "are", "the", "of", "for", "in", "tell", "me", "about", "side", "effects", "uses", "dose", "dosage", "how", "to", "use", "take", "can", "i", "you", "we", "they", "he", "she", "it", "a", "an", "and", "or", "but", "with", "without", "do", "does", "did", "has", "have", "had", "been", "being", "was", "were", "will", "would", "could", "should", "may", "might", "shall", "need", "know", "want", "please", "help", "any", "some", "this", "that", "these", "those"}
        words = q.split()
        meaningful = [w for w in words if w not in stop_words and len(w) > 2]
        if not meaningful:
            return query.strip()
        if len(meaningful) <= 2:
            return " ".join(meaningful)
        return meaningful[-1] if len(meaningful[-1]) > 3 else " ".join(meaningful[-2:])

    def get_structured_info(self, query: str) -> list[dict]:
        results = []
        drug_name = self._extract_drug_name(query)
        search = self.search_1mg(drug_name)
        if not search:
            return results
        for item in search[:2]:
            details = self.get_drug_details(item["url"])
            if details:
                content_parts = []
                if details.get("uses"):
                    content_parts.append("Uses: " + " ".join(details["uses"][:3]))
                if details.get("side_effects"):
                    content_parts.append("Side Effects: " + " ".join(details["side_effects"][:3]))
                results.append({
                    "title": f"1mg: {details.get('name', item['name'])}",
                    "url": item["url"],
                    "content": " | ".join(content_parts),
                    "relevance_score": 0.95,
                })
        return results

    def close(self):
        self.client.close()

    def __del__(self):
        try:
            self.close()
        except Exception:
            pass
