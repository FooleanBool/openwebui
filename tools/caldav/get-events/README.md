# Get Events

A tool for retrieving and formatting calendar events from a CalDAV server. This tool is particularly useful for AI assistants to understand upcoming events and calculate days until specific events.

## Installation

### Installation Steps
1. **Install the Get Events tool:**
   - Navigate to `workspace -> tools -> add tool (+)`
   - Name the function, e.g., "Get Events", and provide a description
   - Save the function

2. **Configure the Valve for Get Events:**
   - Click on the cog icon to open the valve configuration
   - Set the following required parameters:
     - `caldav_url`: Your CalDAV server URL (e.g., "https://your-caldav-server.com")
     - `caldav_user`: Your CalDAV username
     - `caldav_pass`: Your CalDAV password
   - Optional parameters:
     - `num_days`: Number of days to look ahead for events (default: 7)
     - `self_cite`: Whether to include self-citation in output (default: true)

## Usage

### Output Format
The tool returns a formatted string containing:
- Today's date in ISO format
- Day of week information (both integer and string format)
- List of upcoming events with:
  - ISO format start/end times
  - Event summary
  - Event description
  - Event location

### Example Output
```
Today's Date: 2024-03-30 14:30:00+00:00
Today of Week (int): 5
Today of Week (str): Saturday
--------------------------------------------------
Upcoming Calendar Events:

ISO Format Start: 2024-03-30T15:00:00+00:00
Summary: Team Meeting
Description: Weekly sync meeting
Location: Conference Room A
ISO Format End: 2024-03-30T16:00:00+00:00
--------------------------------------------------
```

### Recommended System Prompt for LLMs
When using this tool with an LLM, we recommend including the following system prompt to help the model better understand and process the calendar data:

```
[Tested with gemma3:12b]
You are a calendar-aware AI assistant. When processing calendar events:

1. Date/Time Understanding:
   - All dates are in UTC timezone
   - The "Today's Date" field provides the current reference point
   - Use the ISO format dates for precise calculations
   - The "Today of Week" fields help with relative date understanding

2. Event Processing:
   - Events are sorted chronologically by start time
   - Each event contains: start time, end time, summary, description, and location
   - Pay attention to event durations (difference between start and end times)
   - Consider event descriptions for additional context

3. Response Guidelines:
   - When discussing events, always reference their dates/times clearly
   - Use the event summary as the primary identifier
   - Include relevant location information when available
   - Consider event descriptions for providing additional context
   - If calculating days until an event, use the ISO format dates for accuracy

4. Error Handling:
   - If "No calendars found" is returned, inform the user that no events are available
   - If dates are missing or malformed, acknowledge the uncertainty
   - If event details are incomplete, note what information is available

Remember: All times are in UTC. When discussing times with users, consider converting to their local timezone if known.
```

### Notes
- Events are automatically sorted by start time
- The tool returns "No calendars found" if no calendars are available
- All dates are in UTC timezone
- The tool requires proper CalDAV server credentials to function

## Requirements
- caldav
- icalendar
- pytz

## Error Handling
- Invalid CalDAV credentials will result in connection errors
- Missing required parameters will prevent the tool from functioning
- Network issues will be reported in the output

## Security Considerations
- Store CalDAV credentials securely
- Use environment variables or secure credential storage when possible
- Avoid exposing credentials in logs or error messages 