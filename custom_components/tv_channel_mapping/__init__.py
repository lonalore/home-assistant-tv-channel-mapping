"""The TV Channel Mapping integration."""
from __future__ import annotations

import json
import logging
import os

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .intent import async_setup_intents

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up TV Channel Mapping from a config entry."""
    
    # Set up intents (idempotent registry)
    await async_setup_intents(hass)
    
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

    # Register services
    await async_setup_services(hass, entry)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        # Only remove data if all entries are unloaded (though usually 1 entry per integration instance)
        # For simplicity in this structure we just pop.
        if entry.entry_id in hass.data[DOMAIN]:
            hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


async def update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle options update."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_setup_services(hass: HomeAssistant, entry: ConfigEntry):
    """Register services for the component."""

    async def async_tune_channel(call):
        """Handle the tune_channel service call."""
        channel_name_input = call.data.get("channel_name")
        
        if not channel_name_input:
            _LOGGER.error("No channel name provided")
            return

        # Find the active config entry (assuming one for simplicity, or find associated)
        # Since service is global, we pick the first loaded entry or the one passed setup
        # For this component, typically one instance is used.
        # We can use the entry passed to setup.
        
        data = hass.data[DOMAIN].get(entry.entry_id)
        if not data:
            _LOGGER.error("Integration not loaded properly")
            return

        provider_channels = data.get("base_channels", {})
        
        # Apply Options (Custom channels, renames, deletes)
        options = entry.options
        custom_channels = options.get("custom_channels", {})
        deleted_channels = options.get("deleted_channels", [])
        renamed_channels = options.get("renamed_channels", {})

        # Merge base and custom
        all_channels = provider_channels.copy()
        for ch_num, ch_data in custom_channels.items():
            all_channels[ch_num] = ch_data

        # Filter deleted
        active_channels = {
            k: v for k, v in all_channels.items() 
            if k not in deleted_channels
        }

        # Find target channel number
        target_number = None
        target_name_match = channel_name_input.lower().strip()

        for ch_num, ch_data in active_channels.items():
            # Check original name
            name = ch_data.get("name", "").lower()
            
            # Check rename
            if ch_num in renamed_channels:
                name = renamed_channels[ch_num].lower()
            
            if name == target_name_match:
                target_number = ch_num
                break
        
        if not target_number:
            _LOGGER.warning(f"Channel '{channel_name_input}' not found in active channel list.")
            raise ValueError(f"Channel '{channel_name_input}' not found")

        target_tv = entry.data.get("tv_entity")
        if not target_tv:
             _LOGGER.error("No target TV entity configured")
             return

        _LOGGER.info(f"Service: Tuning {target_tv} to {target_number} ({channel_name_input})")
        
        await hass.services.async_call(
            "media_player",
            "play_media",
            {
                "entity_id": target_tv,
                "media_content_id": target_number,
                "media_content_type": "channel",
            },
        )

    hass.services.async_register(DOMAIN, "tune_channel", async_tune_channel)


def load_json_data(path: str) -> dict:
    """Load JSON data from file."""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)
