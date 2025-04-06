# Quick Image Config

A simple tool for quickly updating image generation settings using shorthand commands.

## Installation

### Installation Steps
1. **Install the Quick Image Config Action Function:**
   - Navigate to `admin settings -> functions -> add function (+)`
   - Name the function, e.g., "Quick Image Config", and provide a description.
   - Save the function.

2. **Configure the Valve for your Quick Image Config:**
   - Click on the cog icon to open the valve configuration.
   - Set the `API Base URL` (e.g., `"https://yourowui.com"` or `"http://localhost:3000"`).
   - Provide your `OWUI API token`.
   - Optionally, enable `Debug` to see debug messages appended to the prompt.

## Usage

### Shorthand Commands
The tool uses simple shorthand commands to update settings:

1. **Model Name:**
   ```
   md:"model name"
   ```
   - Must be in quotes
   - Example: `md:"SDXL 1.0"`

2. **Steps:**
   ```
   st:number
   ```
   - Must be a positive number
   - Example: `st:16`

3. **Dimensions:**
   ```
   dm:widthxheight
   ```
   - Must be in format WxH
   - Example: `dm:768x1344`
   
   Or toggle portrait/landscape:
   ```
   dm:tg
   ```
   - Swaps width and height

### Multiple Updates
You can combine multiple updates in a single input, separated by spaces:
```
st:16 dm:768x1344 md:"SDXL 1.0"
```

### Case Insensitivity
Commands are case-insensitive (except for model names):
```
ST:16 DM:768x1344 md:"Model Name"
```

### Examples
1. **Update steps only:**
   ```
   st:20
   ```

2. **Update dimensions only:**
   ```
   dm:768x1344
   ```

3. **Toggle portrait/landscape:**
   ```
   dm:tg
   ```

4. **Update model only:**
   ```
   md:"SDXL 1.0"
   ```

5. **Full update:**
   ```
   st:20 dm:768x1344 md:"SDXL 1.0"
   ```

### Usage Instructions
1. Click the action button beneath the prompt input.
2. View current settings in the input placeholder.
3. Enter your updates using the shorthand commands.
4. Click `Confirm` and check the status message for confirmation.

### Error Handling
- Invalid commands will show an error message
- Model names must be in quotes
- Steps must be positive numbers
- Dimensions must be in WxH format
- Unknown commands will be rejected

--- 

TODO:
Tidy up line 307, extract string construction to separate function.
 