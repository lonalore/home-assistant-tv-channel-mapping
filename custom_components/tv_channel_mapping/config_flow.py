"""Config flow for TV Channel Mapping integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.selector import EntitySelector, EntitySelectorConfig
import uuid

from .const import DOMAIN, PROVIDERS, CONF_PROVIDER, DEFAULT_PROVIDER, CONF_TV_ENTITY

_LOGGER = logging.getLogger(__name__)


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for TV Channel Mapping."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        if user_input is None:
            return self.async_show_form(
                step_id="user",
                data_schema=vol.Schema(
                    {
                        vol.Required(CONF_PROVIDER, default=DEFAULT_PROVIDER): vol.In(PROVIDERS),
                        vol.Required(CONF_TV_ENTITY): EntitySelector(
                            EntitySelectorConfig(domain="media_player")
                        ),
                    }
                ),
            )

        return self.async_create_entry(title=user_input[CONF_PROVIDER], data=user_input)

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Create the options flow."""
        return OptionsFlowHandler(config_entry)


class OptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options flow."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry
        self.options = dict(config_entry.options)

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        return await self.async_step_menu()

    async def async_step_menu(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Menu for options."""
        return self.async_show_menu(
            step_id="menu",
            menu_options=[
                "select_provider",
                "rename_channel",
                "add_channel",
                "delete_channel"
            ],
        )

    async def async_step_select_provider(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle provider selection."""
        if user_input is not None:
            new_data = dict(self.config_entry.data)
            new_data[CONF_PROVIDER] = user_input[CONF_PROVIDER]
            new_data[CONF_TV_ENTITY] = user_input[CONF_TV_ENTITY]
            
            self.hass.config_entries.async_update_entry(self.config_entry, data=new_data)
            
            # Reset overrides/customizations when switching provider/tv?
            self.hass.config_entries.async_update_entry(self.config_entry, options={})
            return self.async_create_entry(title="", data={})

        current_provider = self.config_entry.data.get(CONF_PROVIDER, DEFAULT_PROVIDER)
        current_tv = self.config_entry.data.get(CONF_TV_ENTITY)

        return self.async_show_form(
            step_id="select_provider",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_PROVIDER, default=current_provider): vol.In(PROVIDERS),
                    vol.Required(CONF_TV_ENTITY, default=current_tv): EntitySelector(
                        EntitySelectorConfig(domain="media_player")
                    ),
                }
            ),
        )

    async def async_step_rename_channel(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Select a channel to rename."""
        # Get active channels (base + custom - deleted)
        channels = self._get_active_channels_dict()

        if not channels:
             return self.async_abort(reason="no_channels")

        if user_input is not None:
            self._selected_channel_id = user_input["channel_id"]
            return await self.async_step_edit_channel_name()

        return self.async_show_form(
            step_id="rename_channel",
            data_schema=vol.Schema(
                {
                    vol.Required("channel_id"): vol.In(channels),
                }
            ),
        )

    async def async_step_edit_channel_name(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Edit the name of the selected channel."""
        if user_input is not None:
            new_name = user_input["new_name"]
            overrides = self.options.get("overrides", {}).copy()
            overrides[self._selected_channel_id] = new_name
            
            new_options = self.options.copy()
            new_options["overrides"] = overrides
            return self.async_create_entry(title="", data=new_options)

        # Get current name
        # We need to look it up again
        channels = self._get_active_channels_dict(include_names=True)
        current_name = channels.get(self._selected_channel_id, "")

        return self.async_show_form(
            step_id="edit_channel_name",
            data_schema=vol.Schema(
                {
                    vol.Required("new_name", default=current_name): str,
                }
            ),
        )

    async def async_step_add_channel(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Add a new custom channel."""
        if user_input is not None:
            name = user_input["name"]
            number = user_input["number"]
            
            # Generate a pseudo ID
            c_id = f"custom-{uuid.uuid4().hex[:8]}"
            
            custom_channels = self.options.get("custom_channels", []).copy()
            custom_channels.append({"id": c_id, "name": name, "number": number})
            
            new_options = self.options.copy()
            new_options["custom_channels"] = custom_channels
            return self.async_create_entry(title="", data=new_options)

        return self.async_show_form(
            step_id="add_channel",
            data_schema=vol.Schema(
                {
                    vol.Required("name"): str,
                    vol.Required("number"): int,
                }
            ),
        )

    async def async_step_delete_channel(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Delete (hide) a channel."""
        channels = self._get_active_channels_dict()
        if not channels:
             return self.async_abort(reason="no_channels")

        if user_input is not None:
            channel_id = user_input["channel_id"]
            
            # If it's a custom channel, remove it entirely
            custom_channels = self.options.get("custom_channels", []).copy()
            original_custom_count = len(custom_channels)
            custom_channels = [c for c in custom_channels if c["id"] != channel_id]
            
            new_options = self.options.copy()
            
            if len(custom_channels) < original_custom_count:
                # It was a custom channel
                new_options["custom_channels"] = custom_channels
            else:
                # It was a base channel, add to deleted list
                deleted = self.options.get("deleted_channels", []).copy()
                if channel_id not in deleted:
                    deleted.append(channel_id)
                new_options["deleted_channels"] = deleted
                
            return self.async_create_entry(title="", data=new_options)

        return self.async_show_form(
            step_id="delete_channel",
            data_schema=vol.Schema(
                {
                    vol.Required("channel_id"): vol.In(channels),
                }
            ),
        )

    def _get_active_channels_dict(self, include_names=False):
        """Helper to get currently active channels as ID -> Name dict (for selection)."""
        domain_data = self.hass.data.get(DOMAIN, {}).get(self.config_entry.entry_id)
        if not domain_data:
            return {}
            
        base_channels = domain_data["base_channels"]
        custom_channels = self.options.get("custom_channels", [])
        deleted_channels = self.options.get("deleted_channels", [])
        overrides = self.options.get("overrides", {})
        
        options = {}
        
        # Add base channels not deleted
        for ch in base_channels:
            if ch["id"] in deleted_channels:
                continue
            name = overrides.get(ch["id"], ch["name"])
            if include_names:
                options[ch["id"]] = name
            else:
                options[ch["id"]] = f"{name} ({ch['number']})"
                
        # Add custom channels
        for ch in custom_channels:
            name = overrides.get(ch["id"], ch["name"]) # Allow renaming custom channels too? Why not.
            if include_names:
                options[ch["id"]] = name
            else:
                 options[ch["id"]] = f"{name} ({ch['number']}) [Custom]"
        
        return options
