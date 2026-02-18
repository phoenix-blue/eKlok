"""API client voor Stedin Eklok."""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any

import requests

_LOGGER = logging.getLogger(__name__)

API_URL = "https://eklok.nl/api/pricedetail"


class StedinEklokAPI:
    """API client voor Stedin Eklok.
    
    De Eklok API retourneert data met:
    - range: -100 (zeer goed/groen) tot +100 (zeer slecht/rood)
    - Negatieve waarden = goed moment om energie te gebruiken
    - Positieve waarden = slecht moment (piek)
    - Data in 5-minuut intervallen
    - Tijden in UTC
    """

    def __init__(self) -> None:
        """Initialiseer de API client."""
        self._session = requests.Session()

    def get_data(self) -> dict[str, Any]:
        """Haal alle data op van de API."""
        today = datetime.now()
        tomorrow = today + timedelta(days=1)
        
        today_data = self._fetch_day(today)
        tomorrow_data = self._fetch_day(tomorrow)
        
        _LOGGER.debug("Today data: %s items", len(today_data) if today_data else 0)
        _LOGGER.debug("Tomorrow data: %s items", len(tomorrow_data) if tomorrow_data else 0)
        
        # Analyseer de data
        today_analysis = self._analyze_day(today_data) if today_data else {}
        tomorrow_analysis = self._analyze_day(tomorrow_data) if tomorrow_data else {}
        
        # Bepaal huidige status
        current_status = self._get_current_status(today_data)
        
        return {
            "today": today_data,
            "tomorrow": tomorrow_data,
            "today_analysis": today_analysis,
            "tomorrow_analysis": tomorrow_analysis,
            "current_status": current_status,
            "last_update": datetime.now().isoformat(),
        }

    def _fetch_day(self, date: datetime) -> list[dict] | None:
        """Haal data op voor een specifieke dag."""
        try:
            params = {"date": date.strftime("%Y-%m-%d")}
            response = self._session.get(API_URL, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            # API retourneert {"data": [...]} structuur
            if isinstance(data, dict) and "data" in data:
                return data["data"]
            elif isinstance(data, list):
                return data
            return None
            
        except requests.RequestException as err:
            _LOGGER.error("Fout bij ophalen data voor %s: %s", date.strftime("%Y-%m-%d"), err)
            return None

    def _analyze_day(self, data: list[dict]) -> dict[str, Any]:
        """Analyseer de data van een dag.
        
        Range interpretatie:
        - range <= -30: Groen (goed moment)
        - range -30 tot +30: Oranje (neutraal)  
        - range >= +30: Rood (slecht moment)
        """
        if not data:
            return {}
        
        ranges = []
        green_moments = []
        orange_moments = []
        red_moments = []
        
        for item in data:
            range_val = item.get("range", 100)
            ranges.append(range_val)
            
            moment_info = {
                "date": item.get("date"),
                "range": range_val,
                "color": item.get("color", self._get_color(range_val)),
            }
            
            # Negatief = goed, Positief = slecht
            if range_val <= -30:
                green_moments.append(moment_info)
            elif range_val <= 30:
                orange_moments.append(moment_info)
            else:
                red_moments.append(moment_info)
        
        # Sorteer beste momenten (laagste/meest negatieve range eerst)
        all_moments = sorted(
            [{"date": d.get("date"), "range": d.get("range", 100)} for d in data],
            key=lambda x: x["range"]
        )
        
        # Groepeer per uur voor hourly_data
        hourly_data = self._aggregate_hourly(data)
        
        # Tel groene uren (uren waar gemiddelde <= -30)
        green_hours = sum(1 for h in hourly_data if h.get("range", 100) <= -30)
        
        return {
            "average_range": round(sum(ranges) / len(ranges), 1) if ranges else 100,
            "min_range": min(ranges) if ranges else 100,
            "max_range": max(ranges) if ranges else 100,
            "green_count": green_hours,  # Aantal groene uren
            "orange_count": sum(1 for h in hourly_data if -30 < h.get("range", 100) <= 30),
            "red_count": sum(1 for h in hourly_data if h.get("range", 100) > 30),
            "best_moments": all_moments[:5],  # Top 5 beste momenten
            "green_moments": green_moments[:10],  # Top 10 groene momenten
            "hourly_data": hourly_data,
            "raw_data_count": len(data),
        }

    def _aggregate_hourly(self, data: list[dict]) -> list[dict]:
        """Aggregeer 5-minuut data naar uur-data."""
        hourly = {}
        
        for item in data:
            try:
                dt_str = item.get("date", "")
                dt = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
                hour = dt.hour
                
                if hour not in hourly:
                    hourly[hour] = {"ranges": [], "colors": []}
                
                hourly[hour]["ranges"].append(item.get("range", 100))
                hourly[hour]["colors"].append(item.get("color", "#ff0000"))
            except (ValueError, TypeError):
                continue
        
        result = []
        for hour in range(24):
            if hour in hourly and hourly[hour]["ranges"]:
                avg_range = sum(hourly[hour]["ranges"]) / len(hourly[hour]["ranges"])
                result.append({
                    "hour": hour,
                    "range": round(avg_range, 1),
                    "color": self._get_color(avg_range),
                })
            else:
                result.append({
                    "hour": hour,
                    "range": None,
                    "color": "gray",
                })
        
        return result

    def _get_current_status(self, today_data: list[dict] | None) -> dict[str, Any]:
        """Bepaal de huidige status op basis van het dichtstbijzijnde datapunt."""
        if not today_data:
            return {"status": "unknown", "range": 100, "color": "gray", "is_good_moment": False}
        
        now_utc = datetime.now(timezone.utc)
        closest_item = None
        min_diff = timedelta(days=1)
        
        for item in today_data:
            try:
                dt_str = item.get("date", "")
                item_dt = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
                diff = abs(now_utc - item_dt)
                
                if diff < min_diff:
                    min_diff = diff
                    closest_item = item
            except (ValueError, TypeError):
                continue
        
        if closest_item:
            range_val = closest_item.get("range", 100)
            return {
                "status": "good" if range_val <= -30 else "moderate" if range_val <= 30 else "bad",
                "range": range_val,
                "color": closest_item.get("color", self._get_color(range_val)),
                "is_good_moment": range_val <= -30,
                "time": closest_item.get("date"),
            }
        
        return {"status": "unknown", "range": 100, "color": "gray", "is_good_moment": False}

    @staticmethod
    def _get_color(range_val: float) -> str:
        """Bepaal de kleur op basis van de range waarde.
        
        Eklok kleuren:
        - Groen (#00ff00): range <= -30 (goed moment)
        - Oranje: range -30 tot +30 (neutraal)
        - Rood (#ff0000): range >= +30 (slecht moment)
        """
        if range_val <= -30:
            return "green"
        elif range_val <= 30:
            return "orange"
        return "red"
