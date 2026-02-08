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

This ensures the AI doesn't need to guess channel numbers.

## Configuration

1. Go to **Settings > Devices & Services**.
2. Click **Configure** on the "TV Channel Mapping" card.
3. Use the menu to:
   - Switch Provider
   - Rename Channels
   - Add Custom Channels
   - Delete Channels
