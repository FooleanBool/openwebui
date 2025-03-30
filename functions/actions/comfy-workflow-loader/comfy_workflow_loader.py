"""
title: ComfyUI Workflow Loader
author: FooleanBool
author_url: https://github.com/FooleanBool
funding_url: https://github.com/FooleanBool
version: 0.2.0
required_open_webui_version: 0.5.1
"""

from pydantic import BaseModel, Field
from typing import Optional, Union, Generator, Iterator
import aiohttp
import asyncio
import json
import os


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

    def __init__(self):
        self.valves = self.Valves()

    def get_auth_headers(self):
        """
        Generates authentication headers for API requests.
        
        Returns:
            dict: Headers dictionary containing:
                - Authorization: Bearer token
                - accept: application/json
                - Content-Type: application/json
        
        The headers are generated dynamically each time to ensure the latest
        authentication token is used.
        """
        return {
            "Authorization": f"Bearer {self.valves.auth_token}",
            "accept": "application/json",
            "Content-Type": "application/json",
        }

    async def action(
        self,
        body: dict,
        __user__=None,
        __event_emitter__=None,
        __event_call__=None,
    ) -> Optional[dict]:
        """
        Main entry point for the ComfyUI workflow loader action.
        
        This method handles the complete workflow of:
        1. Fetching available workflows from the knowledge base
        2. Presenting a selection interface to the user
        3. Parsing and validating the selected workflow
        4. Updating the system configuration with the workflow data
        
        Args:
            body (dict): The request body (currently unused)
            __user__: User context (unused)
            __event_emitter__: Callback for emitting status and debug messages
            __event_call__: Callback for getting user input
        
        Returns:
            Optional[dict]: A dictionary containing the loaded workflow name if successful,
                           None if the operation fails or is cancelled
        
        Example:
            >>> action_instance = Action()
            >>> result = await action_instance.action({})
            >>> print(result)
            {'workflow_name': 'my_workflow'}
        """
        print(f"action:{__name__}")

        # Step 1: Fetch ComfyUI workflows knowledge base by id
        workflows = await self.get_workflows(self.valves.knowledge_base_id)
        if not workflows:
            if __event_emitter__:
                await __event_emitter__(
                    {
                        "type": "status",
                        "data": {
                            "description": "Failed to fetch workflows",
                            "done": True,
                        },
                    }
                )
            return None

        # Create a mapping of filenames without extensions to full filenames
        filename_map = {}
        for file in workflows["files"]:
            base_name = os.path.splitext(file["filename"])[0]
            filename_map[base_name] = file["filename"]

        # Get list of base filenames (without extensions) for display
        base_filenames = list(filename_map.keys())
        filenames_str = "\n".join(base_filenames)

        # Step 2: Show modal with filenames and wait for user input
        if __event_emitter__:
            await __event_emitter__(
                {
                    "type": "status",
                    "data": {"description": "Selecting workflow", "done": False},
                }
            )

        # Debug available workflows
        if __event_emitter__ and self.valves.enable_debug:
            await __event_emitter__(
                {
                    "type": "message",
                    "data": {
                        "content": "\n```debug:\n📋 Available Workflows:\n"
                        + "\n".join(f"• {name}" for name in base_filenames)
                    },
                }
            )

        # Attempts to clear input area below all fail.
        response = await __event_call__(
            {
                "type": "input",
                "data": {
                    "title": "Select Workflow",
                    "message": "Type 3+ chars to match",
                    "placeholder": filenames_str,
                    "value": "",  # Clear the input value
                    "type": "text",  # Explicitly set input type
                    "clearable": True,  # Allow clearing the input
                    "autocomplete": "off",  # Prevent browser from caching the input
                },
            }
        )

        # Debug the response
        if __event_emitter__ and self.valves.enable_debug:
            await __event_emitter__(
                {
                    "type": "message",
                    "data": {"content": f"\n👤 User entered: '{response}'\n```"},
                }
            )

        # Handle partial filename matching
        workflow_base_name = None
        if not response:  # User cancelled or cleared the input
            if __event_emitter__:
                await __event_emitter__(
                    {
                        "type": "status",
                        "data": {"description": "No workflow loaded", "done": True},
                    }
                )
            return None

        response = response.strip()
        if len(response) >= 3:  # Minimum 3 characters required
            # Find all matching filenames that start with the response
            matches = [
                name for name in base_filenames if name.lower().startswith(response.lower())
            ]
            if len(matches) == 1:  # Exact match or unique partial match
                workflow_base_name = matches[0]
            elif len(matches) > 1:  # Multiple matches
                if __event_emitter__:
                    await __event_emitter__(
                        {
                            "type": "status",
                            "data": {
                                "description": f"Multiple matches found: {', '.join(matches)}\nPlease be more specific.",
                                "done": True,
                            },
                        }
                    )
                return None
            else:  # No matches
                if __event_emitter__:
                    await __event_emitter__(
                        {
                            "type": "status",
                            "data": {
                                "description": "No matching workflow found. Please try again.",
                                "done": True,
                            },
                        }
                    )
                return None
        else:
            if __event_emitter__:
                await __event_emitter__(
                    {
                        "type": "status",
                        "data": {
                            "description": "Please enter at least 3 characters.",
                            "done": True,
                        },
                    }
                )
            return None

        if not workflow_base_name or workflow_base_name not in filename_map:
            if __event_emitter__:
                await __event_emitter__(
                    {
                        "type": "status",
                        "data": {"description": "Invalid workflow name", "done": True},
                    }
                )
            return None

        # Get the full filename with extension
        workflow_name = filename_map[workflow_base_name]

        # Step 3: Get file by filename (workflow)
        workflow_data = next(
            (file for file in workflows["files"] if file["filename"] == workflow_name),
            None,
        )
        if (
            not workflow_data
            or "data" not in workflow_data
            or "content" not in workflow_data["data"]
        ):
            if __event_emitter__:
                await __event_emitter__(
                    {
                        "type": "status",
                        "data": {
                            "description": "Failed to retrieve workflow data",
                            "done": True,
                        },
                    }
                )
            return None

        # Step 4: Parse workflow
        if __event_emitter__:
            await __event_emitter__(
                {
                    "type": "status",
                    "data": {"description": "Parsing workflow", "done": False},
                }
            )

        parsed_workflow = self.parse_workflow(workflow_data["data"]["content"])
        if not parsed_workflow:
            if __event_emitter__:
                await __event_emitter__(
                    {
                        "type": "status",
                        "data": {
                            "description": "Failed to parse workflow: Unable to find required node titles.",
                            "done": True,
                        },
                    }
                )
            return None

        # Step 5: Update configurations
        if __event_emitter__:
            await __event_emitter__(
                {
                    "type": "status",
                    "data": {"description": "Updating configurations", "done": False},
                }
            )

        update_success = await self.update_configurations(
            workflow_data["data"]["content"]
        )
        if not update_success:
            if __event_emitter__:
                await __event_emitter__(
                    {
                        "type": "status",
                        "data": {
                            "description": "Failed to update configurations",
                            "done": True,
                        },
                    }
                )
            return None

        # Inform the user of success
        if __event_emitter__:
            await __event_emitter__(
                {
                    "type": "status",
                    "data": {
                        "description": f"Loaded workflow: {workflow_base_name}",
                        "done": True,
                    },
                }
            )

        return {"workflow_name": workflow_base_name}

    async def get_workflows(self, kb_id: str):
        """
        Fetches ComfyUI workflows from the specified knowledge base.
        
        Args:
            kb_id (str): The ID of the knowledge base containing the workflows
        
        Returns:
            Optional[dict]: A dictionary containing the workflows data if successful,
                           None if the request fails
        
        The returned data structure should contain:
        {
            "files": [
                {
                    "filename": str,
                    "data": {
                        "content": str  # JSON string of workflow data
                    }
                }
            ]
        }
        
        Raises:
            aiohttp.ClientError: If the API request fails
            json.JSONDecodeError: If the response is not valid JSON
        """
        url = f"{self.valves.api_base_url}/api/v1/knowledge/{kb_id}"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self.get_auth_headers()) as response:
                    if response.status != 200:
                        print(f"Error fetching workflows: {await response.text()}")
                        return None

                    workflows = await response.json()
                    print(f"Parsed workflows")

                    return workflows
        except Exception as e:
            print(f"Exception in get_workflows: {e}")
            return None

    def parse_workflow(self, workflow_data):
        """
        Parses ComfyUI workflow data to extract required node information.
        
        Args:
            workflow_data (Union[str, dict]): The workflow data as either a JSON string
                                            or a parsed dictionary
        
        Returns:
            Optional[dict]: A dictionary containing parsed workflow data if successful,
                           None if parsing fails
        
        The returned data structure contains:
        {
            "prompt": str,
            "width": int,
            "height": int,
            "model": str,
            "steps": int,
            "seed": int,
            "node_ids": {
                "prompt": str,
                "model": str,
                "width": str,
                "height": str,
                "steps": str,
                "seed": str
            }
        }
        
        Required node titles in the workflow:
        - 'model': Main model loading node (UNETloader)
        - 'positive_prompt': Input prompt node (CLIPTextEncode)
        - 'dimensions': Image dimensions node (EmptySD3LatentImage)
        - 'seed': Random noise node (RandomNoise)
        - 'scheduler': Steps node (BasicScheduler)
        
        Raises:
            ValueError: If required nodes are missing from the workflow
            json.JSONDecodeError: If workflow_data is an invalid JSON string
        """
        try:
            # Load json string if it's a string
            if isinstance(workflow_data, str):
                workflow_data_obj = json.loads(workflow_data)
            else:
                workflow_data_obj = workflow_data

            parsed_data = {
                "prompt": None,
                "width": None,
                "height": None,
                "model": None,
                "steps": None,
                "seed": None,
                "node_ids": {
                    "prompt": None,
                    "model": None,
                    "width": None,
                    "height": None,
                    "steps": None,
                    "seed": None,
                },
            }

            # Required node titles and their corresponding keys
            required_nodes = {
                "positive_prompt": ("prompt", "text"),
                "model": ("model", "unet_name"),
                "dimensions": (["width", "height"], ["width", "height"]),
                "scheduler": ("steps", "steps"),
                "seed": ("seed", "noise_seed"),
            }

            # Track which required nodes were found
            found_nodes = set()

            # Iterate through each node in the workflow
            for node_id, node in workflow_data_obj.items():
                if "_meta" in node and "title" in node["_meta"]:
                    title = node["_meta"]["title"]
                    
                    if title in required_nodes:
                        found_nodes.add(title)
                        target_key, input_key = required_nodes[title]
                        
                        if isinstance(target_key, list):  # Handle multiple outputs (like dimensions)
                            for t_key, i_key in zip(target_key, input_key):
                                parsed_data[t_key] = node["inputs"].get(i_key)
                                parsed_data["node_ids"][t_key] = node_id
                        else:
                            parsed_data[target_key] = node["inputs"].get(input_key)
                            parsed_data["node_ids"][target_key] = node_id

            # Check if all required nodes were found
            missing_nodes = set(required_nodes.keys()) - found_nodes
            if missing_nodes:
                raise ValueError(f"Missing required nodes: {', '.join(missing_nodes)}")

            print(f"Parsed workflow data: {parsed_data}")
            return parsed_data

        except Exception as e:
            print(f"Error parsing workflow data: {e}")
            return None

    async def get_current_config(self):
        """
        Retrieves the current configuration from the API.
        
        Returns:
            Optional[dict]: The current configuration if successful,
                           None if the request fails
        
        The configuration includes settings for:
        - enabled: bool
        - engine: str
        - comfyui: dict
        - openai: dict
        - automatic1111: dict
        - gemini: dict
        
        Raises:
            aiohttp.ClientError: If the API request fails
            json.JSONDecodeError: If the response is not valid JSON
        """
        config_url = f"{self.valves.api_base_url}/api/v1/images/config"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(config_url, headers=self.get_auth_headers()) as response:
                    if response.status != 200:
                        print(f"Error fetching current config: {await response.text()}")
                        return None
                    return await response.json()
        except Exception as e:
            print(f"Exception in get_current_config: {e}")
            return None

    async def update_configurations(self, workflow_data):
        """
        Updates both image and main configurations with the selected workflow data.
        
        This method performs two updates:
        1. Updates the image configuration with model, size, and steps
        2. Updates the main configuration with the ComfyUI workflow data
        
        Args:
            workflow_data (Union[str, dict]): The workflow data to apply
        
        Returns:
            bool: True if both updates succeed, False otherwise
        
        The method preserves all existing configuration values except for the ComfyUI
        section, which is updated with the new workflow data.
        
        Raises:
            aiohttp.ClientError: If any API request fails
            json.JSONDecodeError: If workflow_data is an invalid JSON string
        """
        if not workflow_data:
            return False

        try:
            config_url = f"{self.valves.api_base_url}/api/v1/images/config/update"
            image_config_url = (
                f"{self.valves.api_base_url}/api/v1/images/image/config/update"
            )

            # Create a single session for all requests
            async with aiohttp.ClientSession() as session:
                # Parse workflow data
                parsed_workflow_data = self.parse_workflow(
                    workflow_data
                )  # Call parse_workflow here
                if not parsed_workflow_data:
                    print("Failed to parse workflow data.")
                    return False

                # First update the image config
                image_config = {
                    "MODEL": parsed_workflow_data["model"],
                    "IMAGE_SIZE": f"{parsed_workflow_data['width']}x{parsed_workflow_data['height']}",
                    "IMAGE_STEPS": parsed_workflow_data["steps"],
                }

                # Update image config using POST method
                async with session.post(
                    image_config_url, json=image_config, headers=self.get_auth_headers()
                ) as response:
                    if response.status != 200:
                        print(f"Error updating image config: {await response.text()}")
                        return False

                # Get current configuration
                current_config = await self.get_current_config()
                if not current_config:
                    print("Failed to get current configuration")
                    return False

                # Only update the comfyui section while preserving all other settings
                if "comfyui" not in current_config:
                    current_config["comfyui"] = {}
                
                current_config["comfyui"].update({
                    "COMFYUI_BASE_URL": current_config["comfyui"].get("COMFYUI_BASE_URL", "http://host.docker.internal:8188"),
                    "COMFYUI_API_KEY": current_config["comfyui"].get("COMFYUI_API_KEY", ""),
                    "COMFYUI_WORKFLOW": workflow_data,
                    "COMFYUI_WORKFLOW_NODES": [
                        {
                            "type": "prompt",
                            "key": "text",
                            "node_ids": [parsed_workflow_data["node_ids"]["prompt"]],
                        },
                        {
                            "type": "model",
                            "key": "ckpt_name",
                            "node_ids": [parsed_workflow_data["node_ids"]["model"]],
                        },
                        {
                            "type": "width",
                            "key": "width",
                            "node_ids": [parsed_workflow_data["node_ids"]["width"]],
                        },
                        {
                            "type": "height",
                            "key": "height",
                            "node_ids": [parsed_workflow_data["node_ids"]["height"]],
                        },
                        {
                            "type": "steps",
                            "key": "steps",
                            "node_ids": [parsed_workflow_data["node_ids"]["steps"]],
                        },
                        {
                            "type": "seed",
                            "key": "noise_seed",
                            "node_ids": [parsed_workflow_data["node_ids"]["seed"]],
                        },
                    ],
                })

                # Update main config
                async with session.post(
                    config_url, json=current_config, headers=self.get_auth_headers()
                ) as response:
                    if response.status != 200:
                        print(f"Error updating config: {await response.text()}")
                        return False

                return True  # Indicate success

        except Exception as e:
            print(f"Exception in update_configurations: {e}")
            return False


# Example usage 
if __name__ == "__main__":
    # You can specify the API base URL here if needed
    api_base_url = "http://localhost:3000"
    action_instance = Action()
    asyncio.run(action_instance.action({}))
