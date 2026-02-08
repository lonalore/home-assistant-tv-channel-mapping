"""Constants for the TV Channel Mapping integration."""

DOMAIN = "tv_channel_mapping"

CONF_PROVIDER = "provider"
CONF_CHANNELS = "channels"
CONF_TV_ENTITY = "tv_entity"
CONF_CONTROL_METHOD = "control_method"
CONF_SCRIPT_ENTITY = "script_entity"

METHOD_DIRECT = "direct"
METHOD_SCRIPT = "script"

DEFAULT_PROVIDER = "HU One"
DEFAULT_CONTROL_METHOD = METHOD_DIRECT

PROVIDERS = [
    "HU One",
    "HU Digi",
]

CONTROL_METHODS = [
    METHOD_DIRECT,
    METHOD_SCRIPT,
]
