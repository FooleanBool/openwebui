"""
title: Get Events
author: FooleanBool
author_url: https://github.com/FooleanBool
funding_url: https://github.com/FooleanBool
version: 0.2.0
required_open_webui_version: 0.5.1
requirements: caldav, icalendar, pytz

A tool for retrieving calendar events from a CalDAV server for a specified number of days.
This tool provides formatted output of calendar events including dates, summaries, locations,
and descriptions. It's particularly useful for AI assistants to understand upcoming events
and calculate days until specific events.
"""

from datetime import datetime, timedelta
from pydantic import BaseModel, Field
import caldav
import pytz
from icalendar import Calendar
from typing import Dict, List
from dotenv import load_dotenv
import os


class Tools:
    """
    Main class for handling calendar event retrieval and processing.
    Provides methods to connect to CalDAV servers and format event data.
    """

    class Valves(BaseModel):
        """
        Configuration settings for the calendar event retrieval tool.
        
        Attributes:
            num_days (int): Number of days to look ahead for events (default: 7)
            self_cite (bool): Whether to include self-citation in output (default: True)
            caldav_url (str): URL of the CalDAV server
            caldav_user (str): Username for CalDAV authentication
            caldav_pass (str): Password for CalDAV authentication
        """
        num_days: int = Field(default=7)
        self_cite: bool = Field(default=True)
        caldav_url: str = Field(default="")
        caldav_user: str = Field(default="")
        caldav_pass: str = Field(default="")

    class UserValves(BaseModel):
        """User-specific configuration settings (currently empty)"""
        pass

    def __init__(self):
        """Initialize the Tools class with default valves and citation settings"""
        self.valves = self.Valves()
        self.citation = self.valves.self_cite

    def get_calendar_events(self) -> str:
        """
        Retrieve and format calendar events from a CalDAV server.
        
        This method:
        1. Connects to the configured CalDAV server
        2. Retrieves events for the next n days
        3. Formats event data including dates, summaries, and locations
        4. Returns a structured string with all event information
        
        Returns:
            str: A formatted string containing:
                - Today's date in ISO format
                - Day of week information
                - List of upcoming events with:
                    - ISO format start/end times
                    - Event summary
                    - Event description
                    - Event location
                    
        Note:
            Events are sorted by start time
            Returns "No calendars found" if no calendars are available
        """
        client = caldav.DAVClient(
            url=self.valves.caldav_url,
            username=self.valves.caldav_user,
            password=self.valves.caldav_pass,
        )

        principal = client.principal()
        calendars = principal.calendars()

        if not calendars:
            return "No calendars found"

        start_date = datetime.now(pytz.UTC)
        end_date = start_date + timedelta(days=self.valves.num_days)

        events_list: List[Dict[str, str]] = []

        for calendar in calendars:
            events = calendar.date_search(start=start_date, end=end_date)

            for event in events:
                event_data = Calendar.from_ical(event.data)
                for component in event_data.walk():
                    if component.name == "VEVENT":
                        start_time = component.get("dtstart").dt
                        human_readable_start = start_time.strftime("%Y-%m-%d %H:%M")
                        iso_format_start = start_time.isoformat()

                        end_time = component.get("dtend").dt
                        human_readable_end = end_time.strftime("%Y-%m-%d %H:%M")
                        iso_format_end = end_time.isoformat()

                        event_info = {
                            "iso_format_start": iso_format_start,
                            "summary": component.get("summary", "No title"),
                            "description": component.get(
                                "description", "No description"
                            ),
                            "location": component.get("location", "No location"),
                            "iso_format_end": iso_format_end,
                        }
                        events_list.append(event_info)

        events_list.sort(key=lambda x: x["iso_format_start"])
        output = [f"Today's Date: {start_date}"]
        # output.append(f"Day of Week: {start_date.weekday() + 1}")
        output.append(f"Today of Week (int): {start_date.weekday()}")
        output.append(f"Today of Week (str): {start_date.strftime('%A')}")
        output.append("-" * 50)
        output.append("Upcoming Calendar Events:\n")
        for event in events_list:
            output.extend(
                [
                    f"ISO Format Start: {event['iso_format_start']}",
                    f"Summary: {event['summary']}",
                    f"Description: {event['description']}",
                    f"Location: {event['location']}",
                    f"ISO Format End: {event['iso_format_end']}",
                    "-" * 50,
                ]
            )
        return "\n".join(output)
