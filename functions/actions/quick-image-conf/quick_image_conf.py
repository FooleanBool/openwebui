"""
title: Quick Image Config
author: FooleanBool
author_url: https://github.com/FooleanBool
funding_url: https://github.com/FooleanBool
version: 0.1.0
required_open_webui_version: 0.5.1
icon_url: data:image/svg+xml,%3C%3Fxml%20version%3D%221.0%22%20encoding%3D%22utf-8%22%3F%3E%3C!--%20License%3A%20Apache.%20Made%20by%20bytedance%3A%20https%3A%2F%2Fgithub.com%2Fbytedance%2FIconPark%20--%3E%3Csvg%20width%3D%22800px%22%20height%3D%22800px%22%20viewBox%3D%220%200%2048%2048%22%20fill%3D%22none%22%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%3E%3Crect%20width%3D%2248%22%20height%3D%2248%22%20fill%3D%22white%22%20fill-opacity%3D%220.01%22%2F%3E%3Crect%20x%3D%224%22%20y%3D%226%22%20width%3D%2240%22%20height%3D%2230%22%20rx%3D%222%22%20fill%3D%22%232F88FF%22%2F%3E%3Crect%20x%3D%224%22%20y%3D%226%22%20width%3D%2240%22%20height%3D%2230%22%20rx%3D%222%22%20stroke%3D%22%23000000%22%20stroke-width%3D%224%22%20stroke-linecap%3D%22round%22%20stroke-linejoin%3D%22round%22%2F%3E%3Cpath%20d%3D%22M20%2042H28%22%20stroke%3D%22%23000000%22%20stroke-width%3D%224%22%20stroke-linecap%3D%22round%22%20stroke-linejoin%3D%22round%22%2F%3E%3Cpath%20d%3D%22M34%2042H36%22%20stroke%3D%22%23000000%22%20stroke-width%3D%224%22%20stroke-linecap%3D%22round%22%20stroke-linejoin%3D%22round%22%2F%3E%3Cpath%20d%3D%22M4%2042H6%22%20stroke%3D%22%23000000%22%20stroke-width%3D%224%22%20stroke-linecap%3D%22round%22%20stroke-linejoin%3D%22round%22%2F%3E%3Cpath%20d%3D%22M42%2042H44%22%20stroke%3D%22%23000000%22%20stroke-width%3D%224%22%20stroke-linecap%3D%22round%22%20stroke-linejoin%3D%22round%22%2F%3E%3Cpath%20d%3D%22M12%2042H14%22%20stroke%3D%22%23000000%22%20stroke-width%3D%224%22%20stroke-linecap%3D%22round%22%20stroke-linejoin%3D%22round%22%2F%3E%3C%2Fsvg%3E
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
import aiohttp
import asyncio
import re


class Action:
    class Valves(BaseModel):
        api_base_url: str = Field(
            default="http://localhost:3000",
            description="Base URL for the API server (e.g. http://localhost:3000)",
        )
        auth_token: str = Field(
            description="Authentication token for OWUI API access",
            default="my-owui-api-key"
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

    async def get_current_config(self) -> Optional[Dict[str, Any]]:
        """
        Retrieves the current image configuration from the API.

        Returns:
            Optional[dict]: The current image configuration if successful,
                           None if the request fails

        The configuration includes:
        - MODEL: str
        - IMAGE_SIZE: str (format: "WxH")
        - IMAGE_STEPS: int

        Raises:
            aiohttp.ClientError: If the API request fails
            json.JSONDecodeError: If the response is not valid JSON
        """
        config_url = f"{self.valves.api_base_url}/api/v1/images/image/config"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    config_url, headers=self.get_auth_headers()
                ) as response:
                    if response.status != 200:
                        print(f"Error fetching current config: {await response.text()}")
                        return None
                    return await response.json()
        except Exception as e:
            print(f"Exception in get_current_config: {e}")
            return None

    def parse_input(self, input_str: str) -> Dict[str, Any]:
        """
        Parses the user input string into configuration updates.

        Args:
            input_str (str): User input string in format:
                           "st:16 dm:768x1344 md:\"model name\""
                           or "dm:tg" for dimension toggle

        Returns:
            Dict[str, Any]: Dictionary containing parsed values:
                          {
                              "steps": int,
                              "width": int,
                              "height": int,
                              "model": str
                          }

        Raises:
            ValueError: If input format is invalid or required values are missing
        """
        updates = {}

        # Split input into parts, preserving quoted strings
        parts = []
        current = ""
        in_quotes = False

        for char in input_str:
            if char == '"':
                in_quotes = not in_quotes
            elif char == " " and not in_quotes:
                if current:
                    parts.append(current)
                    current = ""
            else:
                current += char
        if current:
            parts.append(current)

        # Parse each part
        for part in parts:
            if not part:
                continue

            # Convert to lowercase for case-insensitive matching, but preserve original for model name
            cmd = part.lower()
            if cmd.startswith("st:"):
                try:
                    steps = int(part[3:])
                    if steps <= 0:
                        raise ValueError(f"Invalid steps value: {steps}")
                    updates["steps"] = steps
                except ValueError as e:
                    raise ValueError(f"Invalid steps format: {part}")

            elif cmd.startswith("dm:"):
                if part[3:].lower() == "tg":
                    updates["toggle_dimensions"] = True
                else:
                    try:
                        dims = part[3:].split("x")
                        if len(dims) != 2:
                            raise ValueError(f"Invalid dimensions format: {part}")
                        width = int(dims[0])
                        height = int(dims[1])
                        if width <= 0 or height <= 0:
                            raise ValueError(f"Invalid dimensions: {width}x{height}")
                        updates["width"] = width
                        updates["height"] = height
                    except ValueError as e:
                        raise ValueError(f"Invalid dimensions format: {part}")

            elif cmd.startswith("md:"):
                model = part[3:]
                if not model.startswith('"') or not model.endswith('"'):
                    raise ValueError(f"Model name must be in quotes: {part}")
                updates["model"] = model[1:-1]  # Remove quotes

            else:
                raise ValueError(f"Unknown command: {part}")

        return updates

    async def update_config(
        self, updates: Dict[str, Any], current_config: Dict[str, Any]
    ) -> bool:
        """
        Updates the image configuration with new values.

        Args:
            updates (Dict[str, Any]): Dictionary of values to update:
                                    {
                                        "steps": int,
                                        "width": int,
                                        "height": int,
                                        "model": str,
                                        "toggle_dimensions": bool
                                    }
            current_config (Dict[str, Any]): Current configuration to preserve values

        Returns:
            bool: True if update was successful, False otherwise
        """
        try:
            config_url = f"{self.valves.api_base_url}/api/v1/images/image/config/update"

            # Handle dimension toggle
            if updates.get("toggle_dimensions"):
                current_size = current_config.get("IMAGE_SIZE", "512x512").split("x")
                width, height = current_size[1], current_size[0]  # Swap dimensions
            else:
                width = updates.get("width", current_config.get("IMAGE_SIZE", "512x512").split("x")[0])
                height = updates.get("height", current_config.get("IMAGE_SIZE", "512x512").split("x")[1])

            # Always include all required fields, using current values for any not being updated
            update_data = {
                "MODEL": updates.get("model", current_config.get("MODEL", "")),
                "IMAGE_SIZE": f"{width}x{height}",
                "IMAGE_STEPS": updates.get(
                    "steps", current_config.get("IMAGE_STEPS", 20)
                ),
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    config_url, json=update_data, headers=self.get_auth_headers()
                ) as response:
                    if response.status != 200:
                        print(f"Error updating config: {await response.text()}")
                        return False

                return True

        except Exception as e:
            print(f"Exception in update_config: {e}")
            return False

    async def action(
        self,
        body: dict,
        __user__=None,
        __event_emitter__=None,
        __event_call__=None,
    ) -> Optional[dict]:
        """
        Main entry point for the quick image config action.

        This method handles:
        1. Fetching current configuration
        2. Showing current values in modal
        3. Getting user input
        4. Parsing and validating input
        5. Updating configuration

        Args:
            body (dict): The request body (currently unused)
            __user__: User context (unused)
            __event_emitter__: Callback for emitting status and debug messages
            __event_call__: Callback for getting user input

        Returns:
            Optional[dict]: A dictionary containing the updated values if successful,
                           None if the operation fails or is cancelled
        """
        print(f"action:{__name__}")

        # Get current configuration
        current_config = await self.get_current_config()
        if not current_config:
            if __event_emitter__:
                await __event_emitter__(
                    {
                        "type": "status",
                        "data": {
                            "description": "Failed to fetch current configuration",
                            "done": True,
                        },
                    }
                )
            return None

        # Extract current values
        current_values = {
            "model": current_config.get("MODEL", ""),
            "steps": current_config.get("IMAGE_STEPS", 20),
            "width": 512,  # Default values
            "height": 512,
        }

        # Parse dimensions if available
        if "IMAGE_SIZE" in current_config:
            try:
                width, height = map(int, current_config["IMAGE_SIZE"].split("x"))
                current_values["width"] = width
                current_values["height"] = height
            except:
                pass

        # Show current values and get input
        current_info = (
            f"Use Single or space separated updates."
        )

        if __event_emitter__:
            await __event_emitter__(
                {
                    "type": "status",
                    "data": {"description": "Updating configuration", "done": False},
                }
            )

        response = await __event_call__(
            {
                "type": "input",
                "data": {
                    "title": "Quick Image Config",
                    "message": current_info,
                    "placeholder": f"Current Values:\nmd:\"{current_values['model']}\" st:{current_values['steps']} dm:{current_values['width']}x{current_values['height']}\nUse `dm:tg` to toggle portrait/landscape.",
                    "value": "",
                    "type": "text",
                    "clearable": True,
                },
            }
        )

        if not response:
            if __event_emitter__:
                await __event_emitter__(
                    {
                        "type": "status",
                        "data": {"description": "No changes made", "done": True},
                    }
                )
            return None

        try:
            # Handle boolean response (clicking confirm on empty modal)
            if isinstance(response, bool):
                if __event_emitter__:
                    await __event_emitter__(
                        {
                            "type": "status",
                            "data": {"description": "No changes made", "done": True},
                        }
                    )
                return None
                
            # Parse user input
            updates = self.parse_input(response)

            # Update configuration
            success = await self.update_config(updates, current_config)

            if success:
                # Prepare feedback message
                changes = []
                if "steps" in updates:
                    changes.append(f"steps: {updates['steps']}")
                if "model" in updates:
                    changes.append(f"model: {updates['model']}")
                if "toggle_dimensions" in updates:
                    current_size = current_config.get("IMAGE_SIZE", "512x512").split("x")
                    new_width, new_height = current_size[1], current_size[0]
                    changes.append(f"dimensions: {new_width}x{new_height}")
                elif "width" in updates and "height" in updates:
                    changes.append(f"dimensions: {updates['width']}x{updates['height']}")

                status_msg = "Updated: " + ", ".join(changes) if changes else "No changes made"

                if __event_emitter__:
                    await __event_emitter__(
                        {
                            "type": "status",
                            "data": {
                                "description": status_msg,
                                "done": True,
                            },
                        }
                    )
                return updates
            else:
                if __event_emitter__:
                    await __event_emitter__(
                        {
                            "type": "status",
                            "data": {
                                "description": "Failed to update configuration",
                                "done": True,
                            },
                        }
                    )
                return None

        except ValueError as e:
            if __event_emitter__:
                await __event_emitter__(
                    {
                        "type": "status",
                        "data": {
                            "description": f"Invalid input: {str(e)}",
                            "done": True,
                        },
                    }
                )
            return None
        except Exception as e:
            if __event_emitter__:
                await __event_emitter__(
                    {
                        "type": "status",
                        "data": {
                            "description": f"Error: {str(e)}",
                            "done": True,
                        },
                    }
                )
            return None


# Example usage
if __name__ == "__main__":
    action_instance = Action()
    asyncio.run(action_instance.action({}))
