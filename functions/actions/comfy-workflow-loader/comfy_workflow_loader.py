"""
title: ComfyUI Workflow Loader
author: FooleanBool
author_url: https://github.com/FooleanBool
funding_url: https://github.com/open-webui/open-webui
version: 2.0
required_open_webui_version: 0.5.1
icon_url: data:image/svg+xml,%3C%3Fxml%20version%3D%221.0%22%20encoding%3D%22UTF-8%22%3F%3E%3C!--%20License%3A%20Apache.%20Made%20by%20bytedance%3A%20https%3A%2F%2Fgithub.com%2Fbytedance%2FIconPark%20--%3E%3Csvg%20width%3D%22800px%22%20height%3D%22800px%22%20viewBox%3D%220%200%2048%2048%22%20version%3D%221.1%22%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20xmlns%3Axlink%3D%22http%3A%2F%2Fwww.w3.org%2F1999%2Fxlink%22%3E%3Ctitle%3Eworkbench%3C%2Ftitle%3E%3Cdesc%3ECreated%20with%20Sketch.%3C%2Fdesc%3E%3Cg%20id%3D%22workbench%22%20stroke%3D%22none%22%20stroke-width%3D%221%22%20fill%3D%22none%22%20fill-rule%3D%22evenodd%22%3E%3Cg%20id%3D%22%E7%BC%96%E7%BB%84%22%3E%3Crect%20id%3D%22%E7%9F%A9%E5%BD%A2%22%20fill-opacity%3D%220.01%22%20fill%3D%22%23FFFFFF%22%20x%3D%220%22%20y%3D%220%22%20width%3D%2248%22%20height%3D%2248%22%3E%3C%2Frect%3E%3Cpolygon%20id%3D%22Rectangle-55%22%20stroke%3D%22%23000000%22%20stroke-width%3D%224%22%20fill%3D%22%232F88FF%22%20fill-rule%3D%22nonzero%22%20stroke-linejoin%3D%22round%22%20points%3D%2212%2033%204%2033%204%207%2044%207%2044%2033%2036%2033%22%3E%3C%2Fpolygon%3E%3Cpath%20d%3D%22M16%2C22%20L16%2C26%22%20id%3D%22Path-207%22%20stroke%3D%22%23FFFFFF%22%20stroke-width%3D%224%22%20stroke-linecap%3D%22round%22%20stroke-linejoin%3D%22round%22%3E%3C%2Fpath%3E%3Cpath%20d%3D%22M24%2C33%20L24%2C39%22%20id%3D%22Path-207%22%20stroke%3D%22%23000000%22%20stroke-width%3D%224%22%20stroke-linecap%3D%22round%22%20stroke-linejoin%3D%22round%22%3E%3C%2Fpath%3E%3Cpath%20d%3D%22M24%2C18%20L24%2C26%22%20id%3D%22Path-208%22%20stroke%3D%22%23FFFFFF%22%20stroke-width%3D%224%22%20stroke-linecap%3D%22round%22%20stroke-linejoin%3D%22round%22%3E%3C%2Fpath%3E%3Cpath%20d%3D%22M32%2C14%20L32%2C26%22%20id%3D%22Path-209%22%20stroke%3D%22%23FFFFFF%22%20stroke-width%3D%224%22%20stroke-linecap%3D%22round%22%20stroke-linejoin%3D%22round%22%3E%3C%2Fpath%3E%3Cpath%20d%3D%22M12%2C41%20L36%2C41%22%20id%3D%22Path-23%22%20stroke%3D%22%23000000%22%20stroke-width%3D%224%22%20stroke-linecap%3D%22round%22%20stroke-linejoin%3D%22round%22%3E%3C%2Fpath%3E%3C%2Fg%3E%3C%2Fg%3E%3C%2Fsvg%3E
"""

from pydantic import BaseModel, Field
from typing import Optional, Union, Generator, Iterator, Dict, Any, List
import aiohttp
# import asyncio
import json
import os
import logging
import traceback

logger = logging.getLogger(__name__)
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        "%(levelname)s (%(asctime)s): %(message)s (Line: %(lineno)s) [%(funcName)s()]"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
logger.propagate = False
logger.setLevel(logging.ERROR)

REQUIRED_NODES: List[str] = ['model', 'positive_prompt', 'dimensions', 'seed', 'scheduler']


class Action:

    class Valves(BaseModel):
        api_base_url: str = Field(
            default="http://localhost:3000",
            description="Base URL for the API server (e.g. http://localhost:3000)",
        )
        knowledge_base_id: str = Field(
            default="comfy-workflows-knowledge-base-id",
            description="ID of the knowledge base containing ComfyUI workflows",
        )
        auth_token: str = Field(
            default="my-owui-api-key",
            description="Authentication token for OWUI API access",
        )
        enable_debug: bool = Field(
            default=False, description="Enable debug output messages"
        )
        comfyui_url: str = Field(
            default="http://localhost:8188",
            description="URL of the ComfyUI server",
        )
        show_vram: bool = Field(
            default=False,
            description="Show VRAM usage in the workflow selection modal",
        )

    def __init__(self):
        self.valves = self.Valves()

    async def action(
        self,
        body: dict,
        __user__=None,
        __event_emitter__=None,
        __event_call__=None,
    ) -> Optional[dict]:
        """
        Handles workflow loading and configuration updates.
        
        Args:
            body (dict): Action parameters
            user: User object
            __event_emitter__: Event emitter for notifications
            __event_call__: Function to call events
            
        Returns:
            dict|None: Response data or None on error
        """
        print(f"ACTION:{__name__}")

        # Make event emitter available for resuable func
        self.__event_emitter__ = __event_emitter__

        # Used by a few functions and by Parser Class.
        # self.required_nodes = ['model', 'positive_prompt', 'dimensions', 'seed', 'scheduler']
        self.required_nodes: List[str] = REQUIRED_NODES

        # Empty vars for later.
        vram_info: str = ""

        # Is VRAM info enabled?
        if self.valves.show_vram:
            stats: Optional[dict] = await self.get_comfyui_stats()
            if stats is not None:
                vram_info = self.format_vram_info(stats)
            else:
                vram_info = "VRAM info unavailable"
        
        # We need the worflow names.
        workflows = await self.get_workflows(self.valves.knowledge_base_id)
        if not workflows:
            await self.emit_event("Unable to get workflows, exiting.", True)

        filename_map = self.get_file_names(workflows)
        # Prep list of workflows for display
        filenames_str = "\n".join(filename_map.keys())

        # Show the modal.
        response = None
        if callable(__event_call__):
            response = await __event_call__(
                {
                    "type": "input",
                    "data": {
                        "title": "Load Workflow",
                        "message": f"3+ chars or `unload` {':: ' + vram_info if vram_info else ''}",
                        "placeholder": filenames_str,
                    },
                }
            ) # type: ignore
        else:
            logger.error("Event call is not available")

        # Handle user input safely
        if response and isinstance(response, str) and response.strip().lower() == "unload":
            success = await self.unload_models()
            if not success:
                await self.emit_event("Unable to unload models, exiting.", True)
                logger.error("Problem unloading models.")
            # We are done, models unloaded, message sent.
            return
        else:
            # Was it empty?
            if not response:
                await self.emit_event("No changes made.", True)
            # At least 3 chars?
            elif len(response) <= 2:
                await self.emit_event("Input a minimum of three characters.", True)

            # Get the workflow data from the user input, strip newlines, try to match it.
            response = str(response).strip()
            matches: List[str] = [
                name for name in filename_map.keys() if name.lower().startswith(response.lower())
            ]

            if len(matches) == 1:  # Exact match or unique partial match
                workflow_base_name = matches[0]

            # [todo] Need to fix this, "test" and "testing" means "test" cannot be selected."
            elif len(matches) > 1:  # Multiple matches
                await self.emit_event(f"Multiple matches found: {', '.join(matches)}\nPlease be more specific.", True)

            else:
                await self.emit_event("No matching workflow found. Please try again.", True)

            # Need to get the workflow and send to update config
            workflow_id = filename_map[workflow_base_name]
            if not workflow_id:
                await self.emit_event(f"Unable to fetch {workflow_base_name}, exiting.", True)
                logger.error(f"workflow_id: {workflow_id}")

            # Worflow data
            workflow_data = await self.get_workflow(workflow_id)
            if not workflow_data:
                logger.error(f"workflow_data: {workflow_data}")
                await self.emit_event("Unable to fetch workflow, exiting.", True)
            else:
                complete = await self.update_all(workflow_data)
            # Update
            if not complete:
                await self.emit_event("There was a problem :/ Check the logs.", True)
                logger.error(f"complete: {complete}")
            else:
                await self.emit_event(f"Workflow \"{workflow_base_name}\" loaded.", True)
            if self.valves.enable_debug:
                logger.debug(f"RESPONSE: {response}")

    # Update 
    async def update_all(self, workflow_data: dict) -> bool | str:
        """
        Updates image settings and workflow configuration.
        
        Args:
            workflow_data (dict): Workflow data to process
            
        Returns:
            bool | str: True on success, error message or False on failure
        """
        parser = WorkflowParser()
        parsed_workflow_data = parser.parse(workflow_data)
        if not parser.is_complete():
            return f"Workflow missing nodes: {parser.get_missing_nodes()}"
            logger.error(parsed_workflow_data["data"]["content"])

        # Update image config settings
        image_config = {
            "MODEL": parsed_workflow_data["model"]["value"],
            "IMAGE_SIZE": f"{parsed_workflow_data['width']['value']}x{parsed_workflow_data['height']['value']}",
            "IMAGE_STEPS": parsed_workflow_data["steps"]["value"],
        }
        current_config = await self.get_current_config()
        if self.valves.enable_debug:
            logger.debug(f"current_config: {current_config}")
        if not current_config:
            logger.error("Failed to get current configuration")
            return False

        # [IDEA] Could we grab the url to the generated image and add it to the body as a link? 
        # Update the config object

        current_config["comfyui"].update({
            "COMFYUI_BASE_URL": current_config["comfyui"].get("COMFYUI_BASE_URL", "http://host.docker.internal:8188"),
            "COMFYUI_API_KEY": current_config["comfyui"].get("COMFYUI_API_KEY", ""),
            "COMFYUI_WORKFLOW": workflow_data['data']['content'],
            "COMFYUI_WORKFLOW_NODES": [
                {
                    "type": "prompt",
                    "key": "text",
                    "node_ids": [parsed_workflow_data["prompt"]["node_id"]],
                },
                {
                    "type": "model",
                    "key": "ckpt_name",
                    "node_ids": [parsed_workflow_data["model"]["node_id"]],
                },
                {
                    "type": "width",
                    "key": "width",
                    "node_ids": [parsed_workflow_data["width"]["node_id"]],
                },
                {
                    "type": "height",
                    "key": "height",
                    "node_ids": [parsed_workflow_data["height"]["node_id"]],
                },
                {
                    "type": "steps",
                    "key": "steps",
                    "node_ids": [parsed_workflow_data["steps"]["node_id"]],
                },
                {
                    "type": "seed",
                    "key": "noise_seed",
                    "node_ids": [parsed_workflow_data["seed"]["node_id"]],
                },
            ],
        })

        # Try the update.    
        try:
            async with aiohttp.ClientSession() as session:        
                image_config_url = f"{self.valves.api_base_url}/api/v1/images/image/config/update"
                async with session.post(
                    image_config_url, json=image_config, headers=self.get_auth_headers()
                ) as response:
                    if response.status != 200:
                        error_message = await response.text()
                        logger.error(f"Error updating user image settings (status: {response.status}): {error_message}") 
                        return False

                # Image config updated, now comyui workflow etc.
                config_url = f"{self.valves.api_base_url}/api/v1/images/config/update"
                async with session.post(
                    config_url, json=current_config, headers=self.get_auth_headers()
                ) as response:
                    if response.status != 200:
                        error_message = await response.text()
                        logger.error(f"Error updating main configuration (status: {response.status}): {error_message}")
                        return False

        except aiohttp.ClientError as e:
            logger.error(f"Client error in update_all: {e}")
            return False
        # All done, will use pass as seen in other action scripts.
        pass           

    def has_required_node(self, node_title: str) -> bool:
        """
        Checks if a required node exists.

        Args:
            node_title (str): Node title to check

        Returns:
            bool: True if node exists, False otherwise
        """
        # Convert the input node title to lowercase for case-insensitive comparison
        lower_node_title = node_title.lower()

        # Create a list of all required nodes in lowercase
        lower_required_nodes = [node.lower() for node in self.required_nodes]

        # Check if the lowercase node title is in the list of lowercase required nodes
        return lower_node_title in lower_required_nodes


    # Unload models, update messages.

    async def unload_models(self) -> bool:
        try:
            # First check if ComfyUI is running
            if not await self.get_comfyui_stats():
                await self.emit_event("ComfyUI is not running or not accessible", True)
                return True

            payload = {
                "unload_models": True,
                "free_memory": False
            }
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.valves.comfyui_url}/free",
                    json=payload
                ) as response:
                    if response.status == 200:
                        await self.emit_event("Models unloaded successfully", True)
                        return True
                    else:
                        await self.emit_event(f"Failed to unload models: {await response.text()}", True)
                        if self.valves.enable_debug:
                            logger.error(traceback.format_exc())
                        return False

        except aiohttp.ClientError as e:
            logger.error(f"Error unloading models: {str(e)}")
            await self.emit_event(f"Error unloading models: {str(e)}", True)
            return False

    # Re-usable event emitter.
    # await self.emit_event("message", True/False - false is spinner.)
    async def emit_event(self, description: str, done: bool) -> Optional[str]:
        """Emit an event with status update."""
        if not hasattr(self, '__event_emitter__') or self.__event_emitter__ is None:
            logger.error("Warning: __event_emitter__ is not available")
            return

        await self.__event_emitter__(
            {
                "type": "status",
                "data": {"description": description, "done": done},
            }
        )

    # Workflow
    async def get_workflow(self, id: str):
        """
        Fetches a single workflow by ID.
        
        Args:
            id (str): Workflow identifier
            
        Returns:
            Optional[dict]: Workflow data if successful, None otherwise
        """
        url = f"{self.valves.api_base_url}/api/v1/files/{id}"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self.get_auth_headers()) as response:
                    if response.status != 200:
                        logger.error(f"Error fetching workflow: {await response.text()}")
                        return None
                    workflow = await response.json()
                    return workflow
        except Exception as e:
            logger.error(f"Exception in get_workflows: {e}")
            return None

    # Workflows
    async def get_workflows(self, kb_id: str):
        """
        Fetches workflows for specified knowledge base ID.
        
        Args:
            kb_id (str): Knowledge base identifier
            
        Returns:
            Optional[dict]: Workflows data if successful, None otherwise
        """
        url = f"{self.valves.api_base_url}/api/v1/knowledge/{kb_id}"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self.get_auth_headers()) as response:
                    if response.status != 200:
                        logger.error(f"Error fetching workflows: {await response.text()}")
                        return None
                    workflows = await response.json()
                    return workflows
        except Exception as e:
            logger.error(f"Exception in get_workflows: {e}")
            return None

    # Auth
    def get_auth_headers(self) -> dict:
        """Returns authentication headers for API requests."""
        return {
            "Authorization": f"Bearer {self.valves.auth_token}",
            "accept": "application/json",
            "Content-Type": "application/json",
        }

    # Get comfy running status / vram usage. [todo] Update url to use valves.
    async def get_comfyui_stats(self) -> Optional[dict]:
        """
        Gets ComfyUI system statistics including VRAM usage.

        Returns:
            Optional[Dict]: Dictionary containing system stats if successful,
                           None if the request fails
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.valves.comfyui_url}/system_stats",) as response:
                    if response.status == 200:
                        return await response.json()
        except aiohttp.ClientError as e:
            logger.error(f"Error getting ComfyUI stats: {str(e)}")
            return None

    # Format stats for display.
    def format_vram_info(self, stats: dict) -> str:
        """
        Formats VRAM information from system stats into a human-readable string.

        Args:
            stats (Dict): System stats dictionary from ComfyUI

        Returns:
            str: Formatted VRAM information string
        """
        try:
            if not stats or "devices" not in stats or not stats["devices"]:
                return "VRAM info unavailable"

            device = stats["devices"][0]  # Get first CUDA device
            vram_total = device["vram_total"] / (1024**3)  # Convert to GB
            vram_free = device["vram_free"] / (1024**3)  # Convert to GB
            vram_used = vram_total - vram_free
            return f"VRAM: {vram_used:.1f}/{vram_total:.1f} GB used"

        except Exception as e:
            logger.error(f"Error formatting VRAM info: {e}")
            logger.error(traceback.format_exc())
            return "VRAM info unavailable"

    # Get current config for updating.
    async def get_current_config(self):
        """
        Retrieves the current configuration from the API.
        
        Returns:
            Optional[dict]: Configuration data if successful, None otherwise
            
        Raises:
            aiohttp.ClientError: Network request failure
            json.JSONDecodeError: Invalid JSON response
        """
        config_url = f"{self.valves.api_base_url}/api/v1/images/config"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(config_url, headers=self.get_auth_headers()) as response:
                    if response.status != 200:
                        logger.error(f"Error fetching current config: {await response.text()}")
                        return None
                    return await response.json()
        except aiohttp.ClientError as e:
            logger.error(f"Exception in get_current_config: {str(e)}")
            return None

    # Get filenames, and ids.:
    def get_file_names(self, workflows: Optional[dict]) -> dict:
        """Extracts base filenames and their IDs from workflow files."""
        if not workflows:
            return {}

        filename_map = {}
        # Check if 'files' key exists and is iterable
        files = workflows.get('files', [])
        for file in files:
            try:
                base_name = os.path.splitext(file["meta"]["name"])[0]
                filename_map[base_name] = file["id"]
            except (KeyError, TypeError):
                continue
        return filename_map


class WorkflowParser:
    """
    A dedicated parser for ComfyUI workflow data that handles the complexity of
    nested JSON structures and provides a clean interface for extracting configuration data.
    """

    def __init__(self) -> None:
        """Initialize the parser with default required nodes."""
        self.required_nodes: List[str] = REQUIRED_NODES
        self.img_config: Dict[str, Any] = {}

    def parse(self, data: Union[str, Dict[str, Any]]) -> Dict[str, Any]:
        """
        Parse workflow data regardless of format and extract configuration.

        Args:
            data: Either a string (JSON) or dictionary containing workflow data
                 Can be the full document or just the workflow content

        Returns:
            Dictionary containing extracted configuration values
        """
        self.img_config = {}
        # Reset required nodes for new parsing
        self.required_nodes = ['model', 'positive_prompt', 'dimensions', 'seed', 'scheduler']

        # Extract the actual workflow content (nodes)
        workflow_nodes = self._extract_workflow_nodes(data)

        # Process each node
        for node_id, node in workflow_nodes.items():
            if self._is_required_node(node):
                self._process_node(node, node_id)
                # Remove from required list
                if node["_meta"]["title"] in self.required_nodes:
                    self.required_nodes.remove(node["_meta"]["title"])

        return self.img_config

    def _extract_workflow_nodes(self, data: Union[str, Dict[str, Any]]) -> Dict[str, Any]:
        """
        Extract the actual workflow nodes from whatever format the data is in.

        Args:
            data: Input data in various possible formats

        Returns:
            Dictionary of workflow nodes
        """
        # Case 1: String data (JSON)
        if isinstance(data, str):
            try:
                parsed_data = json.loads(data)
                return self._extract_workflow_nodes(parsed_data)  # Recurse with parsed data
            except json.JSONDecodeError:
                raise ValueError("Invalid JSON string provided")

        # Case 2: Full document with data.content as string
        if isinstance(data, dict):
            if 'data' in data and isinstance(data['data'], dict) and 'content' in data['data']:
                content = data['data']['content']
                if isinstance(content, str):
                    try:
                        return json.loads(content)  # Parse the nested JSON string
                    except json.JSONDecodeError:
                        raise ValueError("Invalid JSON in data.content")
                else:
                    return content  # Already a dict

            # Case 3: Already extracted nodes or other dict format
            # Check if this looks like workflow nodes (with _meta keys)
            if any('_meta' in node for node in data.values() if isinstance(node, dict)):
                return data

        # If we get here, we couldn't identify the structure
        raise ValueError("Could not extract workflow nodes from provided data")

    def _is_required_node(self, node: Dict[str, Any]) -> bool:
        """Check if a node is one of the required types."""
        if '_meta' not in node or 'title' not in node['_meta']:
            return False

        title = node['_meta']['title']
        return title.lower() in [n.lower() for n in self.required_nodes]

    def _process_node(self, node: Dict[str, Any], node_id: str) -> None:
        """Extract relevant configuration from a node."""
        title = node["_meta"]["title"]

        match title.lower():
            case 'model':
                self.img_config.update({'model': {
                    'value': node['inputs']['unet_name'],
                    'node_id': node_id}})
            case 'positive_prompt':
                self.img_config.update({'prompt': {
                    'value': node['inputs']['text'],
                    'node_id': node_id}})
            case 'dimensions':
                self.img_config.update({'width': {
                    'value': node['inputs']['width'],
                    'node_id': node_id}})
                self.img_config.update({'height': {
                    'value': node['inputs']['height'],
                    'node_id': node_id}})
            case 'seed':
                self.img_config.update({'seed': {
                    'value': node['inputs']['noise_seed'],
                    'node_id': node_id}})
            case 'scheduler':
                self.img_config.update({'steps': {
                    'value': node['inputs']['steps'],
                    'node_id': node_id}})

    def is_complete(self) -> bool:
        """Check if all required nodes were found."""
        return len(self.required_nodes) == 0

    def get_missing_nodes(self) -> List[str]:
        """Get list of required nodes that were not found."""
        return self.required_nodes
