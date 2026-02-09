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
        await _async_tune_channel_logic(hass, entry, channel_name_input)

    async def async_get_channel_list(call) -> dict:
        """Return a list of available channels."""
        data = hass.data[DOMAIN].get(entry.entry_id)
        if not data:
            raise ValueError("Integration not loaded")

        # Re-use logic to get active map
        options = entry.options
        provider_channels_list = data.get("base_channels", [])
        custom_channels_list = options.get("custom_channels", [])
        deleted_channels = options.get("deleted_channels", [])
        overrides = options.get("overrides", {})

        all_channels_map = {ch["id"]: ch for ch in provider_channels_list}
        for ch in custom_channels_list:
            all_channels_map[ch["id"]] = ch

        active_channels = []
        for c_id, ch_data in all_channels_map.items():
            if c_id not in deleted_channels:
                name = overrides.get(c_id, ch_data["name"])
                active_channels.append(name)
        
        # Sort for better readability for AI
        active_channels.sort()
        
        return {"channels": active_channels}

    import voluptuous as vol
    from homeassistant.core import SupportsResponse

    # VERSION 1.1.4 DEBUG LOG
    _LOGGER.info("TV Channel Mapping: Registering services (v1.1.4) including get_channel_list.")
    
    hass.services.async_register(
        DOMAIN, 
        "tune_channel", 
        async_tune_channel,
        schema=vol.Any(dict)
    )

    hass.services.async_register(
        DOMAIN,
        "get_channel_list",
        async_get_channel_list,
        supports_response=SupportsResponse.ONLY
    )

    # Register LLM Tool if available
    try:
        from homeassistant.helpers import llm
        llm.async_register_tool(hass, TvChannelTool(hass, entry))
    except ImportError:
        _LOGGER.warning("LLM helper not found, automatic AI tool registration skipped.")
    except Exception as e:
        _LOGGER.warning(f"Failed to register LLM tool: {e}")


async def _async_tune_channel_logic(hass: HomeAssistant, entry: ConfigEntry, channel_name_input: str):
    """Reusable logic for tuning the channel."""
    if not channel_name_input:
        _LOGGER.error("No channel name provided")
        raise ValueError("No channel name provided")

    data = hass.data[DOMAIN].get(entry.entry_id)
    if not data:
        _LOGGER.error("Integration not loaded properly")
        raise ValueError("Integration not loaded")

    # Base channels is a LIST of dicts
    provider_channels_list = data.get("base_channels", [])
    
    # Apply Options
    options = entry.options
    custom_channels_list = options.get("custom_channels", [])
    deleted_channels = options.get("deleted_channels", [])
    overrides = options.get("overrides", {}) # Renames are stored here

    # Build a master map keyed by ID to handle merges and deletions easily
    # Start with provider channels
    all_channels_map = {ch["id"]: ch for ch in provider_channels_list}
    
    # Add/Overwrite with custom channels
    for ch in custom_channels_list:
        all_channels_map[ch["id"]] = ch

    # Filter out deleted channels
    active_channels_map = {
        c_id: ch_data for c_id, ch_data in all_channels_map.items()
        if c_id not in deleted_channels
    }

    # Find target channel number
    target_number = None
    target_name_match = channel_name_input.lower().strip()

    # 1. Exact match attempt
    for c_id, ch_data in active_channels_map.items():
        name = overrides.get(c_id, ch_data["name"]).lower()
        if name == target_name_match:
            target_number = ch_data["number"]
            break
            
    # 2. Substring match attempt (New)
    # If the user says "RTL", we should match "RTL HD" or "RTL Klub" before trying fuzzy matching.
    if not target_number:
        for c_id, ch_data in active_channels_map.items():
            name = overrides.get(c_id, ch_data["name"]).lower()
            # Check if input is a word-boundary substring of the channel name
            # e.g. "rtl" in "rtl hd" -> True
            if target_name_match in name.split(): 
                target_number = ch_data["number"]
                _LOGGER.info(f"Substring matched '{channel_name_input}' to '{overrides.get(c_id, ch_data['name'])}'")
                break
            # Also check if it's a prefix (e.g. "film+" matches "film+ hd")
            if name.startswith(target_name_match):
                target_number = ch_data["number"]
                _LOGGER.info(f"Prefix matched '{channel_name_input}' to '{overrides.get(c_id, ch_data['name'])}'")
                break
    
    # 3. Fuzzy match attempt (if exact and substring fail)
    if not target_number:
        import difflib
        # Create a map of name -> number for all active channels
        name_to_number = {}
        for c_id, ch_data in active_channels_map.items():
            name = overrides.get(c_id, ch_data["name"]).lower()
            name_to_number[name] = ch_data["number"]
        
        # Find close matches
        matches = difflib.get_close_matches(target_name_match, name_to_number.keys(), n=1, cutoff=0.6)
        if matches:
            best_match = matches[0]
            target_number = name_to_number[best_match]
            _LOGGER.info(f"Fuzzy matched '{channel_name_input}' to '{best_match}'")

    if not target_number:
        _LOGGER.warning(f"Channel '{channel_name_input}' not found in active channel list.")
        raise ValueError(f"Channel '{channel_name_input}' not found")

    target_tv = entry.data.get("tv_entity")
    if not target_tv:
            _LOGGER.error("No target TV entity configured")
            raise ValueError("No target TV entity configured")

    _LOGGER.info(f"Tuning {target_tv} to {target_number} ({channel_name_input})")
    
    await hass.services.async_call(
        "media_player",
        "play_media",
        {
            "entity_id": target_tv,
            "media_content_id": target_number,
            "media_content_type": "channel",
        },
    )


try:
    from homeassistant.helpers import llm
    import voluptuous as vol

    class TvChannelTool(llm.Tool):
        """LLM Tool for switching TV channels."""

        def __init__(self, hass: HomeAssistant, entry: ConfigEntry):
            """Init the tool."""
            self.hass = hass
            self.entry = entry

        @property
        def metadata(self) -> llm.ToolMetadata:
            """Return metadata for the tool."""
            return llm.ToolMetadata(
                name="tv_channel_mapping_tune_channel",
                description="Switches the TV to a specific channel by its name (e.g., 'RTL', 'HBO', 'Discovery').",
                parameters=vol.Schema({
                    vol.Required("channel_name"): str,
                }),
            )

        async def async_call(self, hass: HomeAssistant, tool_input: llm.ToolInput, llm_context: llm.LLMContext) -> dict:
            """Call the tool."""
            channel_name = tool_input.tool_args.get("channel_name")
            try:
                await _async_tune_channel_logic(hass, self.entry, channel_name)
                return {"result": f"Switched to {channel_name}"}
            except Exception as e:
                return {"error": str(e)}

except ImportError:
    pass

def load_json_data(path: str) -> dict:
    """Load JSON data from file."""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)
