"""Sensor platform voor Stedin Eklok integratie.

De Eklok API werkt met een range van -100 tot +100:
- Negatief (bijv. -57): GOED moment om energie te gebruiken (groen)
- Rond 0: Neutraal moment (oranje)
- Positief (bijv. +93): SLECHT moment, piekbelasting (rood)

Dit is het omgekeerde van wat je zou verwachten!
"""
from __future__ import annotations

from datetime import datetime
import logging
from typing import Any

from homeassistant.components.sensor import (
    SensorEntity,
    SensorDeviceClass,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Stedin Eklok sensors vanuit een config entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    
    sensors = [
        StedinEklokGoodMomentSensor(coordinator, entry),
        StedinEklokCurrentRangeSensor(coordinator, entry),
        StedinEklokTodayBestMomentSensor(coordinator, entry),
        StedinEklokTodayAverageSensor(coordinator, entry),
        StedinEklokTomorrowBestMomentSensor(coordinator, entry),
        StedinEklokTomorrowAverageSensor(coordinator, entry),
        StedinEklokHourlyDataSensor(coordinator, entry),
        StedinEklokGreenCountSensor(coordinator, entry),
    ]
    
    async_add_entities(sensors)


class StedinEklokSensorBase(CoordinatorEntity, SensorEntity):
    """Basis sensor voor Stedin Eklok."""
    
    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialiseer de sensor."""
        super().__init__(coordinator)
        self._entry = entry
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="Stedin Eklok",
            manufacturer="Stedin",
            model="Eklok",
            configuration_url="https://eklok.nl",
        )


class StedinEklokGoodMomentSensor(StedinEklokSensorBase):
    """Binary sensor voor goed moment (Aan/Uit).
    
    Aan = range <= -30 (goed moment, groen)
    Uit = range > -30 (neutraal of slecht moment)
    """
    
    def __init__(self, coordinator: DataUpdateCoordinator, entry: ConfigEntry) -> None:
        """Initialiseer de sensor."""
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_good_moment"
        self._attr_name = "Stedin Eklok Goed Moment"
        self._attr_icon = "mdi:lightning-bolt"
    
    @property
    def native_value(self) -> str:
        """Return of het nu een goed moment is."""
        if self.coordinator.data:
            current = self.coordinator.data.get("current_status", {})
            return "Aan" if current.get("is_good_moment", False) else "Uit"
        return "Uit"
    
    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra attributen."""
        if self.coordinator.data:
            current = self.coordinator.data.get("current_status", {})
            range_val = current.get("range", 100)
            return {
                "range": range_val,
                "color": current.get("color", "gray"),
                "status": current.get("status", "unknown"),
                "uitleg": "Negatieve range = goed moment, Positieve range = slecht moment",
            }
        return {}


class StedinEklokCurrentRangeSensor(StedinEklokSensorBase):
    """Sensor voor huidige range waarde.
    
    Range: -100 (beste) tot +100 (slechtste)
    """
    
    def __init__(self, coordinator: DataUpdateCoordinator, entry: ConfigEntry) -> None:
        """Initialiseer de sensor."""
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_current_range"
        self._attr_name = "Stedin Eklok Huidige Waarde"
        self._attr_icon = "mdi:gauge"
        self._attr_state_class = SensorStateClass.MEASUREMENT
    
    @property
    def native_value(self) -> int:
        """Return de huidige range waarde."""
        if self.coordinator.data:
            current = self.coordinator.data.get("current_status", {})
            return current.get("range", 0)
        return 0
    
    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra attributen."""
        if self.coordinator.data:
            current = self.coordinator.data.get("current_status", {})
            range_val = current.get("range", 0)
            return {
                "color": current.get("color", "gray"),
                "status": current.get("status", "unknown"),
                "is_good_moment": current.get("is_good_moment", False),
                "interpretatie": "goed" if range_val <= -30 else "neutraal" if range_val <= 30 else "slecht",
                "tijd": current.get("time", "unknown"),
            }
        return {}


class StedinEklokTodayBestMomentSensor(StedinEklokSensorBase):
    """Sensor voor het beste moment vandaag."""
    
    def __init__(self, coordinator: DataUpdateCoordinator, entry: ConfigEntry) -> None:
        """Initialiseer de sensor."""
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_today_best"
        self._attr_name = "Stedin Eklok Beste Moment Vandaag"
        self._attr_icon = "mdi:clock-star"
        self._attr_device_class = SensorDeviceClass.TIMESTAMP
    
    @property
    def native_value(self) -> datetime | None:
        """Return het beste moment vandaag."""
        if self.coordinator.data:
            analysis = self.coordinator.data.get("today_analysis", {})
            best = analysis.get("best_moments", [])
            if best:
                try:
                    return datetime.fromisoformat(best[0]["date"].replace("Z", "+00:00"))
                except (ValueError, KeyError, TypeError):
                    return None
        return None
    
    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra attributen."""
        if self.coordinator.data:
            analysis = self.coordinator.data.get("today_analysis", {})
            return {
                "top_3_moments": analysis.get("best_moments", []),
                "green_periods": analysis.get("green_count", 0),
            }
        return {}


class StedinEklokTodayAverageSensor(StedinEklokSensorBase):
    """Sensor voor gemiddelde waarde vandaag.
    
    Lager = beter (negatief is goed).
    """
    
    def __init__(self, coordinator: DataUpdateCoordinator, entry: ConfigEntry) -> None:
        """Initialiseer de sensor."""
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_today_average"
        self._attr_name = "Stedin Eklok Gemiddelde Vandaag"
        self._attr_icon = "mdi:chart-line"
        self._attr_state_class = SensorStateClass.MEASUREMENT
    
    @property
    def native_value(self) -> float | None:
        """Return het gemiddelde van vandaag."""
        if self.coordinator.data:
            analysis = self.coordinator.data.get("today_analysis", {})
            if analysis:
                return analysis.get("average_range")
        return None
    
    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra attributen."""
        if self.coordinator.data:
            analysis = self.coordinator.data.get("today_analysis", {})
            return {
                "min_range": analysis.get("min_range"),
                "max_range": analysis.get("max_range"),
                "groene_uren": analysis.get("green_count", 0),
            }
        return {}


class StedinEklokTomorrowBestMomentSensor(StedinEklokSensorBase):
    """Sensor voor het beste moment morgen."""
    
    def __init__(self, coordinator: DataUpdateCoordinator, entry: ConfigEntry) -> None:
        """Initialiseer de sensor."""
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_tomorrow_best"
        self._attr_name = "Stedin Eklok Beste Moment Morgen"
        self._attr_icon = "mdi:clock-star"
        self._attr_device_class = SensorDeviceClass.TIMESTAMP
    
    @property
    def native_value(self) -> datetime | None:
        """Return het beste moment morgen."""
        if self.coordinator.data:
            analysis = self.coordinator.data.get("tomorrow_analysis", {})
            best = analysis.get("best_moments", [])
            if best:
                try:
                    return datetime.fromisoformat(best[0]["date"].replace("Z", "+00:00"))
                except (ValueError, KeyError, TypeError):
                    return None
        return None
    
    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra attributen."""
        if self.coordinator.data:
            analysis = self.coordinator.data.get("tomorrow_analysis", {})
            return {
                "top_3_moments": analysis.get("best_moments", []),
                "green_periods": analysis.get("green_count", 0),
                "data_available": bool(analysis),
            }
        return {"data_available": False}


class StedinEklokTomorrowAverageSensor(StedinEklokSensorBase):
    """Sensor voor gemiddelde waarde morgen.
    
    Lager = beter (negatief is goed).
    Data is pas beschikbaar als Eklok de prognose publiceert.
    """
    
    def __init__(self, coordinator: DataUpdateCoordinator, entry: ConfigEntry) -> None:
        """Initialiseer de sensor."""
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_tomorrow_average"
        self._attr_name = "Stedin Eklok Gemiddelde Morgen"
        self._attr_icon = "mdi:chart-line"
        self._attr_state_class = SensorStateClass.MEASUREMENT
    
    @property
    def native_value(self) -> float | None:
        """Return het gemiddelde van morgen."""
        if self.coordinator.data:
            analysis = self.coordinator.data.get("tomorrow_analysis", {})
            if analysis and analysis.get("raw_data_count", 0) > 0:
                return analysis.get("average_range")
        return None
    
    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra attributen."""
        if self.coordinator.data:
            analysis = self.coordinator.data.get("tomorrow_analysis", {})
            return {
                "data_beschikbaar": bool(analysis and analysis.get("raw_data_count", 0) > 0),
                "min_range": analysis.get("min_range"),
                "max_range": analysis.get("max_range"),
                "groene_uren": analysis.get("green_count", 0),
            }
        return {"data_beschikbaar": False}


class StedinEklokHourlyDataSensor(StedinEklokSensorBase):
    """Sensor met alle uurdata voor grafieken.
    
    Bevat hourly_today en hourly_tomorrow attributen
    voor gebruik met ApexCharts.
    """
    
    def __init__(self, coordinator: DataUpdateCoordinator, entry: ConfigEntry) -> None:
        """Initialiseer de sensor."""
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_hourly_data"
        self._attr_name = "Stedin Eklok Uurdata"
        self._attr_icon = "mdi:chart-bar"
    
    @property
    def native_value(self) -> str:
        """Return status van de data."""
        if self.coordinator.data:
            return self.coordinator.data.get("last_update", "unknown")
        return "unavailable"
    
    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return alle uurdata als attributen voor grafieken."""
        if not self.coordinator.data:
            return {}
        
        today_analysis = self.coordinator.data.get("today_analysis", {})
        tomorrow_analysis = self.coordinator.data.get("tomorrow_analysis", {})
        
        hourly_today = today_analysis.get("hourly_data", [])
        hourly_tomorrow = tomorrow_analysis.get("hourly_data", [])
        
        return {
            "hourly_today": hourly_today,
            "hourly_tomorrow": hourly_tomorrow,
            "today_count": len([h for h in hourly_today if h.get("range") is not None]),
            "tomorrow_count": len([h for h in hourly_tomorrow if h.get("range") is not None]),
            "interpretatie": "Negatieve waarden = goed, Positieve waarden = slecht",
        }


class StedinEklokGreenCountSensor(StedinEklokSensorBase):
    """Sensor voor aantal groene uren vandaag.
    
    Groene uren = uren waar de gemiddelde range <= -30.
    """
    
    def __init__(self, coordinator: DataUpdateCoordinator, entry: ConfigEntry) -> None:
        """Initialiseer de sensor."""
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_green_count"
        self._attr_name = "Stedin Eklok Groene Uren Vandaag"
        self._attr_icon = "mdi:leaf"
        self._attr_native_unit_of_measurement = "uur"
        self._attr_state_class = SensorStateClass.MEASUREMENT
    
    @property
    def native_value(self) -> int:
        """Return aantal groene uren."""
        if self.coordinator.data:
            analysis = self.coordinator.data.get("today_analysis", {})
            return analysis.get("green_count", 0)
        return 0
    
    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra info over de dagverdeling."""
        if self.coordinator.data:
            analysis = self.coordinator.data.get("today_analysis", {})
            return {
                "oranje_uren": analysis.get("orange_count", 0),
                "rode_uren": analysis.get("red_count", 0),
                "beste_waarde": analysis.get("min_range"),
                "slechtste_waarde": analysis.get("max_range"),
            }
        return {}
