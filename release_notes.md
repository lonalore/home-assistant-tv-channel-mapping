# Release v1.0.0 - Stable Release 🚀

This is the first stable release of the **TV Channel Mapping** integration for Home Assistant!
It allows you to map messy channel names (e.g., "RTL Klub HD") to clean voice commands (e.g., "RTL") and control your TV using natural language or AI.

## 🌟 Key Features

### 📺 Channel Management
- **Pre-configured Providers**: Built-in channel lists for **Digi (HU)** and **Vodafone/UPC (HU)**.
- **Custom Mapping**: Rename channels to whatever you like (e.g., "M4 Sport" -> "Meccs").
- **Smart Tuning**: Automatically finds the right channel number based on your custom names.
- **Ignore List**: Hide channels you never watch so voice commands don't pick them up.

### 🗣️ Voice Control (Assist)
- **Native Support**: Works with Home Assistant's built-in Assist out of the box.
- **Multi-language**: Supports both **Hungarian** 🇭🇺 and **English** 🇺🇸 commands.
  - *"Kapcsold a tévét az RTL-re"*
  - *"Switch TV to HBO"*

### 🤖 AI & LLM Integration
- **Automatic Discovery**: If you use **Extended OpenAI Conversation** (and HA 2024.6+), the integration automatically exposes a "Tune Channel" tool. The AI knows your channel list!
- **Robust Architecture**: The tool registration is fail-safe and won't break on older Home Assistant versions.
- **Manual Fallback**: Detailed guide for manually configuring OpenAI functions if needed.

### 🛠️ Advanced Automation
- **Global Services**:
  - `tv_channel_mapping.tune_channel`: Switch channel by name (great for scripts/automations).
  - `tv_channel_mapping.get_channel_list`: Get a list of all available channels for template sensors or dashboards.

## 📦 Installation
1. Install via **HACS** (Custom Repository).
2. Add the integration in **Settings > Devices & Services**.
3. Select your provider and target TV entity.
4. Enjoy! 🎉

## ❤️ Support
If you like this project, give it a star on GitHub! ⭐
