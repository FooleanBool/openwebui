"""
title: Quick Voice Config
author: FooleanBool
author_url: https://github.com/FooleanBool
funding_url: https://github.com/FooleanBool
version: 0.1.0
required_open_webui_version: 0.5.1
icon_url: data:image/svg+xml,%3C%3Fxml%20version%3D%221.0%22%20encoding%3D%22utf-8%22%3F%3E%3C!--%20License%3A%20Apache.%20Made%20by%20bytedance%3A%20https%3A%2F%2Fgithub.com%2Fbytedance%2FIconPark%20--%3E%3Csvg%20width%3D%22800px%22%20height%3D%22800px%22%20viewBox%3D%220%200%2048%2048%22%20fill%3D%22none%22%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%3E%3Crect%20width%3D%2248%22%20height%3D%2248%22%20fill%3D%22white%22%20fill-opacity%3D%220.01%22%2F%3E%3Cpath%20d%3D%22M24%2044C35.0457%2044%2044%2035.0457%2044%2024C44%2012.9543%2035.0457%204%2024%204C12.9543%204%204%2012.9543%204%2024C4%2035.0457%2012.9543%2044%2024%2044Z%22%20fill%3D%22%232F88FF%22%20stroke%3D%22%23000000%22%20stroke-width%3D%224%22%2F%3E%3Cpath%20d%3D%22M30%2018V30%22%20stroke%3D%22white%22%20stroke-width%3D%224%22%20stroke-linecap%3D%22round%22%2F%3E%3Cpath%20d%3D%22M36%2022V26%22%20stroke%3D%22white%22%20stroke-width%3D%224%22%20stroke-linecap%3D%22round%22%2F%3E%3Cpath%20d%3D%22M18%2018V30%22%20stroke%3D%22white%22%20stroke-width%3D%224%22%20stroke-linecap%3D%22round%22%2F%3E%3Cpath%20d%3D%22M12%2022V26%22%20stroke%3D%22white%22%20stroke-width%3D%224%22%20stroke-linecap%3D%22round%22%2F%3E%3Cpath%20d%3D%22M24%2014V34%22%20stroke%3D%22white%22%20stroke-width%3D%224%22%20stroke-linecap%3D%22round%22%2F%3E%3C%2Fsvg%3E
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
import aiohttp
import asyncio


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
        """
        return {
            "Authorization": f"Bearer {self.valves.auth_token}",
            "accept": "application/json",
            "Content-Type": "application/json",
        }

    async def get_current_settings(self) -> Optional[Dict[str, Any]]:
        """
        Retrieves the current user settings from the API.
        """
        settings_url = f"{self.valves.api_base_url}/api/v1/users/user/settings"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    settings_url, headers=self.get_auth_headers()
                ) as response:
                    if response.status != 200:
                        print(f"Error fetching current settings: {await response.text()}")
                        return None
                    return await response.json()
        except Exception as e:
            print(f"Exception in get_current_settings: {e}")
            return None

    def parse_input(self, input_str: str) -> Dict[str, Any]:
        """
        Parses the user input string into settings updates.
        Format examples:
        - vc:bm_lewis(2)+am_adam(1)
        - sp:1.5
        - ap:tg
        """
        updates = {}
        parts = input_str.split()

        for part in parts:
            if not part:
                continue

            cmd = part.lower()
            if cmd.startswith("vc:"):
                voice = part[3:]
                updates["voice"] = voice
            elif cmd.startswith("sp:"):
                try:
                    speed = float(part[3:])
                    if not 0.5 <= speed <= 2.0:
                        raise ValueError(f"Speed must be between 0.5 and 2.0: {speed}")
                    updates["playback_rate"] = speed
                except ValueError as e:
                    raise ValueError(f"Invalid speed format: {part}")
            elif cmd.startswith("ap:"):
                if part[3:].lower() == "tg":
                    updates["toggle_autoplay"] = True
                else:
                    raise ValueError(f"Invalid autoplay command: {part}")
            else:
                raise ValueError(f"Unknown command: {part}")

        return updates

    async def update_settings(
        self, updates: Dict[str, Any], current_settings: Dict[str, Any]
    ) -> bool:
        """
        Updates the user settings with new values while preserving all other settings.
        """
        try:
            settings_url = f"{self.valves.api_base_url}/api/v1/users/user/settings/update"

            # Deep copy the current settings to avoid modifying the original
            update_data = current_settings.copy()

            # Get current TTS settings
            current_tts = current_settings.get("ui", {}).get("audio", {}).get("tts", {})
            
            # Update only the TTS settings that need to change
            if "voice" in updates or "playback_rate" in updates:
                if "ui" not in update_data:
                    update_data["ui"] = {}
                if "audio" not in update_data["ui"]:
                    update_data["ui"]["audio"] = {}
                if "tts" not in update_data["ui"]["audio"]:
                    update_data["ui"]["audio"]["tts"] = current_tts.copy()

                update_data["ui"]["audio"]["tts"].update({
                    "voice": updates.get("voice", current_tts.get("voice", "")),
                    "playbackRate": updates.get("playback_rate", current_tts.get("playbackRate", 1.0)),
                    "engineConfig": current_tts.get("engineConfig", {"dtype": "fp16"}),
                    "defaultVoice": current_tts.get("defaultVoice", "am_adam")
                })

            # Handle autoplay toggle
            if updates.get("toggle_autoplay"):
                if "ui" not in update_data:
                    update_data["ui"] = {}
                current_autoplay = current_settings.get("ui", {}).get("responseAutoPlayback", False)
                update_data["ui"]["responseAutoPlayback"] = not current_autoplay

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    settings_url, json=update_data, headers=self.get_auth_headers()
                ) as response:
                    if response.status != 200:
                        print(f"Error updating settings: {await response.text()}")
                        return False

            return True

        except Exception as e:
            print(f"Exception in update_settings: {e}")
            return False

    async def action(
        self,
        body: dict,
        __user__=None,
        __event_emitter__=None,
        __event_call__=None,
    ) -> Optional[dict]:
        """
        Main entry point for the quick voice config action.
        """
        print(f"action:{__name__}")

        # Get current settings
        current_settings = await self.get_current_settings()
        if not current_settings:
            if __event_emitter__:
                await __event_emitter__(
                    {
                        "type": "status",
                        "data": {
                            "description": "Failed to fetch current settings",
                            "done": True,
                        },
                    }
                )
            return None

        # Extract current values
        current_tts = current_settings.get("ui", {}).get("audio", {}).get("tts", {})
        current_values = {
            "voice": current_tts.get("voice", ""),
            "playback_rate": current_tts.get("playbackRate", 1.0),
            "autoplay": current_settings.get("ui", {}).get("responseAutoPlayback", False)
        }

        # Show current values and get input
        current_info = (

            f"Use space-separated commands to update:"
        )

        if __event_emitter__:
            await __event_emitter__(
                {
                    "type": "status",
                    "data": {"description": "Updating settings", "done": False},
                }
            )

        response = await __event_call__(
            {
                "type": "input",
                "data": {
                    "title": "Quick Voice Config",
                    "message": current_info,
                    "placeholder": f"Current Settings:\nvc:{current_values['voice']} sp:{current_values['playback_rate']} ap: {'On' if current_values['autoplay'] else 'Off'}\nUse `ap:tg` to toggle autoplay",
                    "value": "",
                    "type": "text",
                    "clearable": True,
                },
            }
        )

        if not response:  # User cancelled or cleared the input
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
                
            # Ensure response is a string before parsing
            if not isinstance(response, str):
                response = str(response)
                
            # Parse user input
            updates = self.parse_input(response)

            # Update settings
            success = await self.update_settings(updates, current_settings)

            if success:
                # Prepare feedback message
                changes = []
                if "voice" in updates:
                    changes.append(f"voice: {updates['voice']}")
                if "playback_rate" in updates:
                    changes.append(f"speed: {updates['playback_rate']}")
                if "toggle_autoplay" in updates:
                    new_autoplay = not current_values["autoplay"]
                    changes.append(f"autoplay: {'On' if new_autoplay else 'Off'}")

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
                                "description": "Failed to update settings",
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