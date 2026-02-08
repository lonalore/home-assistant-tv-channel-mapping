"""The TV Channel Mapping integration."""
from __future__ import annotations

import json
import logging
import os

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up TV Channel Mapping from a config entry."""
    
    # Load the provider data
    provider = entry.data.get("provider")
    # Convert 'HU One' to 'hu_one'
    filename = provider.lower().replace(" ", "_")
    data_path = os.path.join(os.path.dirname(__file__), "data", f"{filename}.json")
    
    _LOGGER.debug(f"Loading data from {data_path} for provider {provider}")

    try:
        channels_data = await hass.async_add_executor_job(load_json_data, data_path)
    except FileNotFoundError:
        _LOGGER.error(f"Provider data file not found: {data_path}")
        return False
    except json.JSONDecodeError:
        _LOGGER.error(f"Invalid JSON in provider data file: {data_path}")
        return False

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {
        "provider": provider,
        "base_channels": channels_data["channels"]
    }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    entry.async_on_unload(entry.add_update_listener(update_listener))

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


async def update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle options update."""
    await hass.config_entries.async_reload(entry.entry_id)


def load_json_data(path: str) -> dict:
    """Load JSON data from file."""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)
