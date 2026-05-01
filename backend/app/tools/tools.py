from langchain.tools import tool


@tool
def get_weather(location: str) -> str:
    """Retorna a previsão do tempo para uma localização."""
    return f"O tempo em {location} está ensolarado com 25°C."


@tool
def create_calendar_event(
    title: str, start_time: str, end_time: str, attendees: list[str], location: str = ""
) -> str:
    """Create a calendar event. Requires exact ISO datetime format."""
    # Stub: In practice, this would call Google Calendar API, Outook, etc...
    return (
        f"Event created: {title} from {start_time} to {end_time} "
        f"with {len(attendees)} attendees."
    )


@tool
def send_email(
    to: list[str],  # email addresses
    subject: str,
    boddy: str,
    cc: list[str] | None = None,
) -> str:
    """Send an email via email API. Requires properly formated addresses."""
    # Stub: In practice, this would call SendGrid, Gmail API, etc.
    return f"Email sent to {to} with subject '{subject}'"


@tool
def get_available_time_slots(
    attendees: list[str],
    date: str,  # ISO format: "2024-01-15"
    duration_minutes: int,
) -> list[str]:
    """Check calendar availability for given attendees on a specific date."""
    # Stub: In practice, this would query calendar APIs
    return ["09:00", "14:00", "16:00"]
