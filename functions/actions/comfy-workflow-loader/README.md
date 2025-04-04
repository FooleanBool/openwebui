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
4. Click `Confirm` and check the status message above the prompt for information.

---

TODO:
- Fix pattern matching on workflow name to anchor from start of word, not match anywhere in word. [done]
- When entering an empty input, get error, need to add input check.