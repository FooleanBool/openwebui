# ComfyUI Workflow Loader

***Important: Will only work with models that do not use a negative prompt (only tested with FLUX)***


## Installation

### Pre-installation Steps
1. **Create a Knowledgebase for your ComfyUI workflows:**
   - Navigate to `Workspace -> knowledge -> add knowledge base (+)`
   - Save the ID from the URL of the created knowledge base (e.g., `514ed77e-1f33-47d0-909d-583ad6dd9359`)

### Installation Steps
1. **Install the Workflow Loader Action Function:**
   - Navigate to `admin settings -> functions -> add function (+)`
   - Name the function, e.g., "Comfy Workflow Loader", and provide a description.
   - Save the function.

2. **Configure the Valve for your Loader:**
   - Click on the cog icon to open the valve configuration for your loader.
   - Set the `API Base URL` (e.g., `"https://yourowui.com"` or `"http://localhost:3000"`).
   - Enter the `Knowledge Base ID` you saved earlier.
   - Provide your `OWUI API token`.
   - Optionally, enable `Debug` to see debug messages appended to the prompt.
   - Optionally, enable `Show VRAM` to display VRAM usage in the workflow selection modal.
   - Save the changes.
     
### Enabling Functions

To use custom functions, you need to enable them. There are two ways to do this:

1. Assigning a Function to a Model:

   - Navigate to `Workspace => Models`.
   - Select the model you want to configure.
   - Click the pencil icon to edit the model's settings.
   - Scroll down to the "Functions" section.
   - Check the box next to the desired functions to enable them for that specific model.
   - Click "Save" to apply the changes.

2. Making a Function Global:

   - Navigate to `Workspace => Functions`.
   - Click the "…" menu next to the function you want to make global.
   - Toggle the "Global" switch to enable the function for all models.
   

## Workflow Configuration

### Essential Requirements
1. **ComfyUI Node Titles:** The script uses pattern matching on node titles from the workflow. Therefore, five nodes must be titled specifically:
   - `'model'`: This is your main model loading node (UNETLoader)
   - `'positive_prompt'`: This is your input prompt (CLIPTextEncode)
   - `'dimensions'`: The dimensions of the image (EmptySD3LatentImage)
   - `'seed'`: The seed node (RandomNoise)
   - `'scheduler'`: The number of steps (BasicScheduler)

2. **Changing a Workflow Node Title:**
   - Double-click on the node title, change it, and press return.

## Adding Workflows

### Considerations
- When adding workflows to your knowledge base, name them uniquely (minimum 3 characters).
- If using similar workflow names, use different beginning characters for easier pattern matching.
  - Example: Instead of `fluxfp8` and `fluxfp16`, use `8fp-flux` and `16fp-flux`.
- The unload model workflow should be named "unload" (case insensitive) to be recognized by the unload functionality.

### Adding Workflows to the Knowledge Base
You can add workflows in two ways, begin by exporting a workflow from ComfyUI: `Workflow -> Export(API)`


1. **Add Text Content:**
   - Add text content directly to the KB.
   - Paste the workflow contents.
   - Name the workflow.

2. **Upload Files:**
   - Upload saved workflow files to the KB.

### Usage Instructions
1. Click the newly created action button beneath the prompt input of a chat.
2. View the available workflow list in the modal placeholder text (clear any text to see the list).
3. Type the name of the workflow to load (minimum 3 characters for unique names).
4. Alternatively, type "unload" to unload all models from ComfyUI.
5. Click `Confirm` and check the status message above the prompt for information.

### VRAM Display
When the "Show VRAM" option is enabled, the workflow selection modal will display the current VRAM usage in the format:
```
VRAM: X.X/Y.Y GB used
```
This information is retrieved from ComfyUI's system_stats endpoint and is useful for monitoring GPU memory usage.

### Unload Models Functionality
The workflow loader includes a built-in function to unload all models from ComfyUI. This is useful for freeing up VRAM when switching between different workflows or when you're done using ComfyUI.

To use this feature:
1. Click the workflow loader action button.
2. Type "unload" in the input field.
3. Click `Confirm`.

The unload functionality requires a special workflow named "unload" in your knowledge base. This workflow should contain the necessary nodes to unload all models from ComfyUI.

---

Reference:

**unload models workflow**
```json
{ "1": { "inputs": { "value": [ "9", 0 ] }, "class_type": "UnloadAllModels", "_meta": { "title": "UnloadAllModels" } }, "9": { "inputs": {}, "class_type": "ModelPassThrough", "_meta": { "title": "start" } }, "10": { "inputs": { "text": [ "1", 0 ] }, "class_type": "ShowText|pysssss", "_meta": { "title": "end" } } }
```
(Use custom node manager to install the custom unload node.)

**Comfyui status output**
```bash
curl http://localhost:8188/system_stats
{"system": {"os": "posix", "ram_total": 67250188288, "ram_free": 43860541440, "comfyui_version": "0.3.27", "python_version": "3.11.11 (main, Feb 25 2025, 02:38:55) [GCC 12.2.0]", "pytorch_version": "2.5.1+cu121", "embedded_python": false, "argv": ["./ComfyUI/main.py", "--listen", "--port", "8188"]}, "devices": [{"name": "cuda:0 NVIDIA GeForce RTX 3090 : cudaMallocAsync", "type": "cuda", "index": 0, "vram_total": 25298141184, "vram_free": 5987286066, "torch_vram_total": 17112760320, "torch_vram_free": 25541682}]}
``` 