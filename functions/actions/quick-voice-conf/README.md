# Quick Voice Config

A simple tool for quickly updating voice settings using shorthand commands.

> **Note:** Quick voice config requires a chat refresh for voice changes to take effect, quickest way is to switch to another chat and back again. [issue](https://github.com/open-webui/open-webui/issues/12193) 
This tool was built and tested specifically for the Kokoro FastAPI implementation. While it may work with other Open WebUI implementations, it has not been tested with them.


## Installation

### Installation Steps
1. **Install the Quick Voice Config Action Function:**
   - Navigate to `admin settings -> functions -> add function (+)`
   - Name the function, e.g., "Quick Voice Config", and provide a description.
   - Save the function.

2. **Configure the Valve for your Quick Voice Config:**
   - Click on the cog icon to open the valve configuration.
   - Set the `API Base URL` (e.g., `"https://yourowui.com"` or `"http://localhost:3000"`).
   - Provide your `OWUI API token`.
   - Optionally, enable `Debug` to see debug messages appended to the prompt.

## Usage

### Shorthand Commands
The tool uses simple shorthand commands to update settings:

1. **Voice:**
   ```
   vc:voice_name
   ```
   - Example: `vc:bm_lewis(2)+am_adam(1)`

2. **Speed:**
   ```
   sp:number
   ```
   - Must be between 0.5 and 2
   - Example: `sp:1.5`

3. **Auto-playback:**
   ```
   ap:tg
   ```
   - Toggles auto-playback on/off

### Multiple Updates
You can combine multiple updates in a single input, separated by spaces:
```
vc:bm_lewis(2)+am_adam(1) sp:1.5 ap:tg
```

### Case Insensitivity
Commands are case-insensitive:
```
VC:voice_name SP:1.5 AP:tg
```

### Examples
1. **Update voice only:**
   ```
   vc:bm_lewis(2)+am_adam(1)
   ```

2. **Update speed only:**
   ```
   sp:1.5
   ```

3. **Toggle auto-playback:**
   ```
   ap:tg
   ```

4. **Full update:**
   ```
   vc:bm_lewis(2)+am_adam(1) sp:1.5 ap:tg
   ```

### Usage Instructions
1. Click the action button beneath the prompt input.
2. View current settings in the input placeholder.
3. Enter your updates using the shorthand commands.
4. Click `Confirm` and check the status message for confirmation.

### Error Handling
- Invalid commands will show an error message
- Speed must be between 0.5 and 2
- Unknown commands will be rejected
- Invalid auto-playback command will be rejected

--- 
