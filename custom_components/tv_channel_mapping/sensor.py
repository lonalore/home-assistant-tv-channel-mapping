"""Sensor platform for TV Channel Mapping."""
from __future__ import annotations

import logging

from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, CONF_PROVIDER

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the TV Channel Mapping sensor."""
    async_add_entities([TVChannelMappingSensor(hass, entry)])


class TVChannelMappingSensor(SensorEntity):
    """Representation of a TV Channel Mapping Sensor."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the sensor."""
        self._hass = hass
        self._entry = entry
        self._attr_name = "TV Channel Mapping"
        self._attr_unique_id = f"{entry.entry_id}_mapping"
        self._attr_icon = "mdi:television-guide"

    @property
    def state(self) -> str:
        """Return the state of the sensor (Current Provider)."""
        return self._entry.data.get(CONF_PROVIDER, "Unknown")

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the state attributes (The Mapping)."""
        domain_data = self._hass.data[DOMAIN][self._entry.entry_id]
        base_channels = domain_data["base_channels"]
        
        overrides = self._entry.options.get("overrides", {})
        custom_channels = self._entry.options.get("custom_channels", [])
        deleted_channels = self._entry.options.get("deleted_channels", [])
        
        mapping = {}
        
        # Process base channels
        for ch in base_channels:
            c_id = ch["id"]
            if c_id in deleted_channels:
                continue
            
            # Get overridden name or default name
            c_name = overrides.get(c_id, ch["name"])
            c_number = ch["number"]
            
            mapping[c_name] = c_number

        # Process custom channels
        for ch in custom_channels:
            c_id = ch["id"]
            # Custom channels can also be overridden (renamed) or deleted (though usually deleted means removed from list)
            # But let's check overrides just in case user renamed a custom channel
            c_name = overrides.get(c_id, ch["name"])
            c_number = ch["number"]
            
            mapping[c_name] = c_number
            
        return {"channels": mapping, "provider": self.state}

    @property
    def should_poll(self) -> bool:
        """No polling needed."""
        return False
