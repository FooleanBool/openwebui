"""
title: Quick Voice Config
author: FooleanBool
author_url: https://github.com/FooleanBool
funding_url: https://github.com/FooleanBool
version: 0.1.0
required_open_webui_version: 0.5.1
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
        Updates the user settings with new values.
        """
        try:
            settings_url = f"{self.valves.api_base_url}/api/v1/users/user/settings/update"

            # Get current TTS settings
            current_tts = current_settings.get("ui", {}).get("audio", {}).get("tts", {})
            
            # Prepare update data
            update_data = {
                "ui": {
                    "audio": {
                        "tts": {
                            "voice": updates.get("voice", current_tts.get("voice", "")),
                            "playbackRate": updates.get("playback_rate", current_tts.get("playbackRate", 1.0)),
                            "engineConfig": current_tts.get("engineConfig", {"dtype": "fp16"}),
                            "defaultVoice": current_tts.get("defaultVoice", "am_adam")
                        }
                    }
                }
            }

            # Handle autoplay toggle
            if updates.get("toggle_autoplay"):
                current_autoplay = current_settings.get("ui", {}).get("responseAutoPlayback", False)
                update_data["ui"]["responseAutoPlayback"] = not current_autoplay
            else:
                update_data["ui"]["responseAutoPlayback"] = current_settings.get("ui", {}).get("responseAutoPlayback", False)

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
            f"Current settings:\n"
            f"Voice: {current_values['voice']}\n"
            f"Speed: {current_values['playback_rate']}\n"
            f"Autoplay: {'On' if current_values['autoplay'] else 'Off'}\n\n"
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
                    "placeholder": f"vc:{current_values['voice']} sp:{current_values['playback_rate']} ap:tg",
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