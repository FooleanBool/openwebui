# Get Tasks

A tool for retrieving and formatting calendar tasks (todos) from a CalDAV server. This tool is particularly useful for AI assistants to understand and manage task lists and track task completion.

> **Note:** CalDAV tasks are implemented as VTODO components in the iCalendar format. This tool specifically handles these todo items from your CalDAV server.

## Installation

### Installation Steps
1. **Install the Get Tasks Action Function:**
   - Navigate to `admin settings -> functions -> add function (+)`
   - Name the function, e.g., "Get Tasks", and provide a description
   - Save the function

2. **Configure the Valve for Get Tasks:**
   - Click on the cog icon to open the valve configuration
   - Set the following required parameters:
     - `caldav_url`: Your CalDAV server URL (e.g., "https://your-caldav-server.com")
     - `caldav_user`: Your CalDAV username
     - `caldav_pass`: Your CalDAV password
   - Optional parameters:
     - `include_completed`: Whether to include completed tasks in output (default: false)
     - `self_cite`: Whether to include self-citation in output (default: true)

## Usage

### Example Instantiation
```python
from tools.caldav.get_tasks import Tools

# Create an instance of the Tools class
task_tool = Tools()

# Configure the tool with your CalDAV credentials
task_tool.valves.caldav_url = "https://your-caldav-server.com"
task_tool.valves.caldav_user = "your_username"
task_tool.valves.caldav_pass = "your_password"
task_tool.valves.include_completed = False  # Optional: exclude completed tasks

# Get calendar tasks
tasks = task_tool.get_calendar_tasks()
```

### Output Format
The tool returns a formatted string containing:
- Today's date in ISO format
- Day of week information (both integer and string format)
- List of tasks with:
  - Summary
  - Status
  - Priority (if set)
  - Due date (if set)
  - Completion date (if completed)
  - Categories (if any)
  - Description

### Example Output
```
Today's Date: 2024-03-30 14:30:00+00:00
Today of Week (int): 5
Today of Week (str): Saturday
--------------------------------------------------
Calendar Tasks:

Summary: Complete project documentation
Status: NEEDS-ACTION
Priority: 1
Due Date: 2024-04-01T23:59:59+00:00
Categories: work, documentation
Description: Write comprehensive documentation for the new feature
--------------------------------------------------
```

### Recommended System Prompt for LLMs
When using this tool with an LLM, we recommend including the following system prompt to help the model better understand and process the task data:

```
You are a task management AI assistant. When processing calendar tasks:

1. Task Status Understanding:
   - Tasks can have status: NEEDS-ACTION, COMPLETED, CANCELLED, or IN-PROCESS
   - Completed tasks are typically excluded by default
   - Pay attention to status changes and completion dates

2. Priority and Due Date Processing:
   - Priority is a number (higher = more important)
   - Tasks are sorted by priority (higher first) and then by due date
   - Due dates are in UTC timezone
   - Missing due dates are treated as lowest priority

3. Task Organization:
   - Categories help group related tasks
   - Tasks can have multiple categories
   - Use categories to understand task context and relationships

4. Response Guidelines:
   - When discussing tasks, always reference their priority and due date
   - Use the task summary as the primary identifier
   - Include relevant categories when grouping or organizing tasks
   - Consider task descriptions for providing additional context
   - If calculating time until due, use the ISO format dates for accuracy

5. Task Management:
   - Help identify high-priority tasks that need immediate attention
   - Group tasks by category when appropriate
   - Consider due dates when suggesting task order
   - Note when tasks are overdue or approaching their due date

Remember: All times are in UTC. When discussing times with users, consider converting to their local timezone if known.
```

### Notes
- Tasks are automatically sorted by priority (higher numbers first) and then by due date
- The tool returns "No tasks found" if no calendars are available
- Completed tasks are excluded by default unless include_completed is True
- All dates are in UTC timezone

## Requirements
- caldav
- icalendar
- pytz
- pydantic

## Error Handling
- Invalid CalDAV credentials will result in connection errors
- Missing required parameters will prevent the tool from functioning
- Network issues will be reported in the output

## Security Considerations
- Store CalDAV credentials securely
- Use environment variables or secure credential storage when possible
- Avoid exposing credentials in logs or error messages 