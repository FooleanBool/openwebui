"""
title: Get Tasks
author: FooleanBool
author_url: https://github.com/FooleanBool
funding_url: https://github.com/FooleanBool
version: 0.1.0
required_open_webui_version: 0.5.1
requirements: caldav, icalendar, pytz, pydantic

A tool for retrieving and formatting calendar tasks (todos) from a CalDAV server.
This tool provides structured output of tasks including summaries, status,
priorities, due dates, and descriptions. It's particularly useful for AI
assistants to understand and manage task lists and track task completion.
"""

from datetime import datetime, timedelta
from pydantic import BaseModel, Field
import caldav
import pytz
from icalendar import Calendar
from typing import Dict, List, Optional
from dotenv import load_dotenv
import os


class Tools:
    """
    Main class for handling calendar task retrieval and processing.
    Provides methods to connect to CalDAV servers and format task data.
    """

    class Valves(BaseModel):
        """
        Configuration settings for the calendar task retrieval tool.
        
        Attributes:
            include_completed (bool): Whether to include completed tasks in output (default: False)
            self_cite (bool): Whether to include self-citation in output (default: True)
            caldav_url (str): URL of the CalDAV server
            caldav_user (str): Username for CalDAV authentication
            caldav_pass (str): Password for CalDAV authentication
        """
        include_completed: bool = Field(default=False)
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

    def get_calendar_tasks(self) -> str:
        """
        Retrieve and format calendar tasks from a CalDAV server.
        
        This method:
        1. Connects to the configured CalDAV server
        2. Retrieves all tasks (optionally including completed ones)
        3. Formats task data including status, priority, due dates, and descriptions
        4. Returns a structured string with all task information
        
        Returns:
            str: A formatted string containing:
                - Today's date in ISO format
                - Day of week information
                - List of tasks with:
                    - Summary
                    - Status
                    - Priority (if set)
                    - Due date (if set)
                    - Completion date (if completed)
                    - Categories (if any)
                    - Description
                    
        Note:
            Tasks are sorted by priority (higher numbers first) and then by due date
            Returns "No tasks found" if no calendars are available
            Completed tasks are excluded by default unless include_completed is True
        """
        client = caldav.DAVClient(
            url=self.valves.caldav_url,
            username=self.valves.caldav_user,
            password=self.valves.caldav_pass,
        )

        principal = client.principal()
        calendars = principal.calendars()

        if not calendars:
            return "No tasks found"

        start_date = datetime.now(pytz.UTC)
        tasks_list: List[Dict[str, any]] = []

        for calendar in calendars:
            todos = calendar.todos()

            for todo in todos:
                todo_data = Calendar.from_ical(todo.data)
                for component in todo_data.walk():
                    if component.name == "VTODO":
                        # Get task status
                        status = component.get("status", "NEEDS-ACTION")

                        # Skip completed tasks if not included
                        if status == "COMPLETED" and not self.valves.include_completed:
                            continue

                        # Handle due date
                        due_date = component.get("due")
                        due_iso = None
                        if due_date:
                            if isinstance(due_date.dt, datetime):
                                due_iso = due_date.dt.isoformat()
                            else:
                                # If it's just a date, convert to datetime
                                due_iso = (
                                    datetime.combine(due_date.dt, datetime.min.time())
                                    .replace(tzinfo=pytz.UTC)
                                    .isoformat()
                                )

                        # Handle completion date
                        completed_date = component.get("completed")
                        completed_iso = None
                        if completed_date:
                            if isinstance(completed_date.dt, datetime):
                                completed_iso = completed_date.dt.isoformat()

                        task_info = {
                            "summary": component.get("summary", "No title"),
                            "status": status,
                            "description": component.get(
                                "description", "No description"
                            ),
                            "priority": component.get("priority", 0),
                            "categories": component.get("categories", []),
                            "due_date": due_iso,
                            "completed_date": completed_iso,
                            "created": component.get("created", ""),
                        }
                        tasks_list.append(task_info)

        # Sort tasks by priority (higher numbers first) and then by due date
        tasks_list.sort(
            key=lambda x: (
                -1 * (x["priority"] or 0) if x["priority"] else 0,
                x["due_date"] if x["due_date"] else "9999-12-31T23:59:59+00:00",
            )
        )

        output = [f"Today's Date: {start_date}"]
        output.append(f"Today of Week (int): {start_date.weekday()}")
        output.append(f"Today of Week (str): {start_date.strftime('%A')}")
        output.append("-" * 50)
        output.append("Calendar Tasks:\n")

        for task in tasks_list:
            output.extend(
                [
                    f"Summary: {task['summary']}",
                    f"Status: {task['status']}",
                ]
            )
            if task["priority"]:
                output.append(f"Priority: {task['priority']}")
            if task["due_date"]:
                output.append(f"Due Date: {task['due_date']}")
            if task["completed_date"]:
                output.append(f"Completed: {task['completed_date']}")
            if task["categories"]:
                output.append(f"Categories: {', '.join(task['categories'])}")
            output.extend(
                [
                    f"Description: {task['description']}",
                    "-" * 50,
                ]
            )

        return "\n".join(output)
