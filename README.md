# Home Assistant TV Channel Mapping

A HACS integration to manage TV channel mappings. 

It comes with presets for Hungarian providers (HU One, HU Digi), but supports **custom channel lists** via the "Add Channel" feature, allowing you to build your own mapping for any provider.

## Features

- **Select Provider**: Choose your TV provider during configuration.
- **Channel Mapping**: Automatically loads channel numbers based on the selected provider.
- **Customization**: Rename channels to your liking via Options.
- **Sensor**: Exposes a `sensor.tv_channel_mapping` with attributes containing the full map (Name -> Number) for use in automations and scripts.

## Installation

### Option 1: HACS (Recommended)
1.  Open HACS in Home Assistant.
2.  Go to "Integrations" section.
3.  Click the 3 dots in the top right corner -> **Custom repositories**.
4.  Add the URL of this repository.
5.  Category: **Integration**.
6.  Click **Add**.
7.  Now search for "TV Channel Mapping" in HACS and install it.
8.  Restart Home Assistant.

### Option 2: Manual
1.  Download the repository.
2.  Copy the `custom_components/tv_channel_mapping` folder to your Home Assistant `config/custom_components/` directory.
3.  Restart Home Assistant.

## Configuration
1.  Go to **Settings -> Devices & Services**.
2.  Click **Add Integration** button.
3.  Search for **TV Channel Mapping** and select it.
4.  Select your provider (e.g., HU Digi or HU One).
5.  Select the **Target TV** (The `media_player` entity you want to control).

## Usage

### Voice Control
The integration automatically registers voice commands (English and Hungarian). You can control the configured TV by saying:

- *"Switch TV to RTL"*
- *"Change to channel TV2"*
- *"Put on Discovery Channel"*

The channel name is matched against your active channel list.

### Sensor Entity

The integration creates `sensor.tv_channel_mapping`. The state is the current provider name. The attributes contain the channel mapping.

Example Automation Action:
```yaml
service: media_player.play_media
target:
  entity_id: media_player.my_tv
data:
  media_content_id: "{{ state_attr('sensor.tv_channel_mapping', 'channels')['RTL'] }}"
  media_content_type: channel
```
