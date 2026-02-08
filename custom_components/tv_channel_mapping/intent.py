"""Intent handler for TV Channel Mapping."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers import intent
from homeassistant.config_entries import ConfigEntry

from .const import DOMAIN, CONF_TV_ENTITY

_LOGGER = logging.getLogger(__name__)

INTENT_SWITCH_CHANNEL = "TvChannelSwitch"


async def async_setup_intents(hass: HomeAssistant) -> None:
    """Set up intents for the integration."""
    intent.async_register(hass, SwitchChannelIntent())


class SwitchChannelIntent(intent.IntentHandler):
    """Handle switching TV channels."""

    intent_type = INTENT_SWITCH_CHANNEL
    slot_schema = {
        "channel_name": str,
    }

    async def async_handle(self, intent_obj: intent.Intent) -> intent.IntentResponse:
        """Handle the intent."""
        hass = intent_obj.hass
        slots = self.async_validate_slots(intent_obj.slots, self.slot_schema)
        channel_name_raw = slots["channel_name"]["value"].lower()

        # Handle Hungarian suffixes (-ra, -re)
        # Examples: rtl-re, tv2-re, hbo-ra
        channel_name_clean = channel_name_raw
        if channel_name_raw.endswith("-re"):
             channel_name_clean = channel_name_raw[:-3]
        elif channel_name_raw.endswith("-ra"):
             channel_name_clean = channel_name_raw[:-3]
        elif channel_name_raw.endswith("re") and len(channel_name_raw) > 2:
             # Basic heuristic for "RTLre" (if STT misses hyphen)
             channel_name_clean = channel_name_raw[:-2]
        elif channel_name_raw.endswith("ra") and len(channel_name_raw) > 2:
             channel_name_clean = channel_name_raw[:-2]

        _LOGGER.debug("Received intent to switch channel. Raw: %s, Cleaned: %s", channel_name_raw, channel_name_clean)

        # Iterate over all config entries to find the channel
        # Assumption: User likely has only one TV Channel Mapping entry active.
        
        entry = None
        target_number = None
        target_tv = None
        
        if DOMAIN not in hass.data:
            raise intent.IntentHandleError("Integration not loaded")

        for entry_id, data in hass.data[DOMAIN].items():
            cfg_entry = hass.config_entries.async_get_entry(entry_id)
            if not cfg_entry:
                continue

            target_tv = cfg_entry.data.get(CONF_TV_ENTITY)
            if not target_tv:
                continue

            # Reconstruct mapping (logic duped from sensor.py, ideally refactor)
            base_channels = data["base_channels"]
            overrides = cfg_entry.options.get("overrides", {})
            custom_channels = cfg_entry.options.get("custom_channels", [])
            deleted_channels = cfg_entry.options.get("deleted_channels", [])

            found_number = None
            
            # Helper to check match
            def check_match(name_to_check):
                name_norm = name_to_check.lower()
                # Exact match against raw or clean
                if name_norm == channel_name_raw: 
                    return True
                if name_norm == channel_name_clean:
                    return True
                return False

            # Check base
            for ch in base_channels:
                if ch["id"] in deleted_channels:
                    continue
                c_name = overrides.get(ch["id"], ch["name"])
                if check_match(c_name):
                    found_number = ch["number"]
                    break
            
            # Check custom
            if found_number is None:
                for ch in custom_channels:
                    c_name = overrides.get(ch["id"], ch["name"])
                    if check_match(c_name):
                        found_number = ch["number"]
                        break
            
            if found_number is not None:
                target_number = found_number
                entry = cfg_entry
                break
        
        if target_number is None:
            raise intent.IntentHandleError(f"Channel '{channel_name_clean}' not found.")

        _LOGGER.info("Switching %s to channel %s (%s)", target_tv, channel_name, target_number)

        # Call the service
        await hass.services.async_call(
            "media_player",
            "play_media",
            {
                "entity_id": target_tv,
                "media_content_id": target_number,
                "media_content_type": "channel",
            },
        )

        response = intent_obj.create_response()
        response.async_set_speech(f"Switched to {channel_name}")
        return response
