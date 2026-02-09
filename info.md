# Home Assistant TV Channel Mapping

{% if installed %}
## Thank you for installing!
{% endif %}

Manage TV channel mappings in Home Assistant. Includes presets for **HU One** and **HU Digi**, but allows creating completely **custom channel lists** as well.

## Features

- **Select Provider**: Choose from built-in presets or create your own list.
- **Channel Mapping**: Automatically creates a sensor with attributes for all channels.
- **Voice Control**: Native support for Home Assistant Assist (e.g., "Kapcsold a tévét az RTL-re").
- **Customization**:
  - **Add Custom Channels**: Build your own channel list from scratch or extend the presets.
  - **Rename**: Rename channels to your liking (e.g., "RTL" -> "RTL Klub").
  - **Delete**: Hide channels you don't use.
- **Easy Updates**: Switch providers or target TV at any time via the UI.

## Usage

### Voice Control (Assist)
Just say:
- *"Switch TV to RTL"*
- *"Change to channel TV2"*
- *"Put on BBC News"*

The integration automatically creates `sensor.tv_channel_mapping`.
- **State**: The name of the currently selected provider.
- **Attributes**: A dictionary of channels (`Name: Number`).

### Example Automation

```yaml
service: media_player.play_media
target:
  entity_id: media_player.living_room_tv
data:
  media_content_id: "{{ state_attr('sensor.tv_channel_mapping', 'channels')['RTL Klub'] }}"
  media_content_type: channel
```

### External Control (OpenAI / Scripts)
For advanced use cases (like Extended OpenAI Conversation), use the dedicated service:
*   **Service**: `tv_channel_mapping.tune_channel`
*   **Data**: `channel_name: "RTL"`

**Automatic Discovery**: If you use Home Assistant 2024.6 or newer, this integration automatically registers a "Tune Channel" tool for AI agents. You likely don't need any extra setup!

**Prompt Example**:
> "Use `tv_channel_mapping.tune_channel` when the user asks to change the TV channel. Pass the channel name as the argument. If you are unsure about the channel name, or if the user asks for a list, use `tv_channel_mapping.get_available_channels` first."

#### Method B: Direct Function Configuration (Best for Extended OpenAI)
If automatic discovery doesn't work, you can explicitly define the function in **Extended OpenAI Conversation** settings under the **Functions** section:

```yaml
- spec:
    name: tune_channel
    description: Switches the TV to a specific channel by name.
    parameters:
      type: object
      properties:
        channel_name:
          type: string
          description: The name of the channel (e.g. RTL, HBO).
      required:
        - channel_name
  function:
    type: script
    sequence:
      - service: tv_channel_mapping.tune_channel
        data:
          channel_name: "{{ channel_name }}"

- spec:
    name: get_available_channels
    description: Returns a list of available TV channels.
  function:
    type: script
    sequence:
      - service: tv_channel_mapping.get_channel_list
        response_variable: _function_result
```
This allows the AI to control the TV directly without any scripts.

## Configuration

1. Go to **Settings > Devices & Services**.
2. Click **Configure** on the "TV Channel Mapping" card.
3. Use the menu to:
   - Switch Provider
   - Rename Channels
   - Add Custom Channels
   - Delete Channels

## Support

If you enjoy this integration, please consider buying me a coffee! ☕

[![Buy Me A Coffee](https://img.shields.io/badge/Buy%20Me%20A%20Coffee-Donate-FFDD00.svg?style=for-the-badge&logo=buymeacoffee&logoColor=black)](https://buymeacoffee.com/lonalore)
