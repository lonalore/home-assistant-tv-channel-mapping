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

**Manual Script Setup (Recommended Fallback)**:
If automatic discovery doesn't work, create a script manually:

1.  Go to **Settings > Automations & Scenes > Scripts**.
2.  Create a new Script (**Add Script**).
3.  Click the 3 dots (top right) -> **Edit in YAML**.
4.  Paste this code:

```yaml
alias: TV Channel Control
description: Switches the TV to a specific channel.
fields:
  channel_name:
    description: Name of the channel (e.g. RTL, HBO)
    example: RTL
sequence:
  - action: tv_channel_mapping.tune_channel
    data:
      channel_name: "{{ channel_name }}"
```

5.  Save the script.
6.  **Expose** it to your Voice Assistant (Settings > Voice Assistants > Assist > Expose).
7.  **System Prompt**: Update your AI's instructions:
    > "You have access to a script called `script.tv_channel_control`. Use it whenever the user asks to change the TV channel. Pass the channel name (e.g., 'RTL', 'TV2') as the `channel_name` argument."

## Configuration

1. Go to **Settings > Devices & Services**.
2. Click **Configure** on the "TV Channel Mapping" card.
3. Use the menu to:
   - Switch Provider
   - Rename Channels
   - Add Custom Channels
   - Delete Channels
