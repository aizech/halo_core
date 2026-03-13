# Configuration

The Configuration hub is the central place for app setup, split into tabs for different settings areas.

---

## What It Does

- Customize app appearance and behavior
- Configure sources and connectors
- Set chat options and presets
- Adjust studio template settings
- Access advanced agent controls

---

## Configuration Tabs

| Tab | Purpose |
|-----|---------|
| **App** | Design, menu, theme, sidebar behavior |
| **Sources** | Connectors, image model |
| **Chat** | Logging, presets, model/tools/team |
| **Studio** | Template settings |
| **Advanced** | Agent-level controls |

---

## App Tab

### Design Settings

- **Colors**: Background, text, hover, separator
- **Icon size**: Size of UI icons
- **Font size**: Base font size

### Menu Settings

- **Sidebar width**: Collapsed and expanded widths
- **Menu entries**: Order and item types
- **Item types**: Link, spacer, separator, theme toggle

### Branding

- **Light logo**: Logo for light mode
- **Dark logo**: Logo for dark mode
- **Light icon**: Favicon for light mode
- **Dark icon**: Favicon for dark mode

---

## Sources Tab

### Connectors

- Enable/disable connectors
- Configure connector credentials
- Set fetch behavior

### Image Model

- Select image generation model
- Configure model parameters

---

## Chat Tab

### Logging Options

- **Agent payload logs**: Log request payloads
- **Agent response logs**: Log responses
- **Agent error logs**: Log errors
- **User request logs**: Log user inputs
- **Stream event logs**: Log streaming events

### Presets

- Select from saved presets
- Apply model/tools/member bundle in one step

### Model and Tools

- Select AI model
- Enable/disable tools
- Configure team members

---

## Studio Tab

### Template Settings

- Default language
- Default tone
- Output format preferences

---

## Advanced Tab

Access via **Open Agent Config** button.

### Agent Configuration

- Per-agent settings
- Tools selection
- MCP server list
- Role instructions
- Coordination mode

---

## Saving Configuration

### In-Section Save

1. Make changes in a section
2. Click the section's save button
3. Changes persist immediately

### Global Settings

Some settings require app restart:

- Data directory changes
- Memory backend toggle
- Major theme changes

---

## Configuration Files

Configuration is stored in:

| File | Content |
|------|---------|
| `config.json` | App settings |
| `presets.json` | Chat presets |
| `data/agents/*.json` | Agent configurations |
| `templates/studio_templates.json` | Studio templates |

---

## Best Practices

### Before Changing Settings

- Note current values
- Test with small changes first
- Save working configurations

### After Changing Settings

- Verify behavior in affected areas
- Check for error messages
- Document custom configurations

---

## Troubleshooting

### "Preset list is empty"

Cause: `presets.json` missing or invalid.

Try this:

1. Add a valid `presets.json` in project root
2. Reopen Configuration → Chat

### "Configuration doesn't save"

Possible causes:

- File permissions issue
- Invalid value format
- Disk space issue

Try this:

1. Check file permissions
2. Verify value formats
3. Ensure disk space available

### "Changes don't take effect"

Try this:

1. Save the configuration
2. Refresh the app (R key)
3. Restart if necessary

---

## Next Steps

- [Advanced Usage](advanced.md) — Deep customization
- [Admin Configuration](../admin/configuration.md) — System-level settings
