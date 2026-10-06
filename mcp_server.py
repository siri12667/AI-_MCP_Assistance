from mcp.server.fastmcp import FastMCP

mcp = FastMCP("ai-personal-assistant")

# -----------------------------
# Weather Tool
# -----------------------------

@mcp.tool()
def get_weather(city: str) -> str:
    """Get the current weather for a city."""

    fake_weather = {
        "Hyderabad": "30 C, sunny",
        "Bangalore": "25 C, cloudy",
        "Chennai": "32 C, humid",
        "Mumbai": "29 C, partly cloudy",
        "Delhi": "28 C, clear",
        "London": "15 C, drizzle",
        "Tokyo": "22 C, clear",
        "New York": "10 C, partly cloudy",
    }

    return fake_weather.get(
        city,
        f"No weather data available for {city}."
    )


# -----------------------------
# Notes
# -----------------------------

NOTES = []


@mcp.tool()
def add_note(text: str) -> str:
    """Save a note for the user."""

    NOTES.append(text)

    return f"Note saved successfully: {text}"


@mcp.tool()
def list_notes() -> str:
    """Return all saved notes."""

    if not NOTES:
        return "No notes have been saved."

    return "\n".join(
        f"{i + 1}. {note}"
        for i, note in enumerate(NOTES)
    )


@mcp.tool()
def clear_notes() -> str:
    """Delete all saved notes."""

    NOTES.clear()

    return "All notes have been cleared."


# -----------------------------
# Calculator
# -----------------------------

@mcp.tool()
def calculator(expression: str) -> str:
    """Calculate a basic arithmetic expression."""

    try:
        allowed = {
            "__builtins__": {}
        }

        result = eval(expression, allowed)

        return f"Result: {result}"

    except Exception:
        return "Unable to calculate that expression."


# -----------------------------
# Resource
# -----------------------------

@mcp.resource("notes://all")
def all_notes_resource() -> str:
    """Read all saved notes as a resource."""

    return list_notes()


# -----------------------------
# Prompt
# -----------------------------

@mcp.prompt()
def daily_briefing(city: str) -> str:
    """Create a prompt for a daily briefing."""

    return (
        f"Give me a short daily briefing for {city}. "
        f"Use the get_weather tool to check the weather "
        f"and use the list_notes tool to check my saved notes."
    )


# -----------------------------
# Start MCP Server
# -----------------------------

if __name__ == "__main__":
    mcp.run()