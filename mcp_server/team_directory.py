from mcp.server.mcpserver import MCPServer

mcp = MCPServer("team-directory")

PEOPLE = {
    "ali@meetdesk.test":  {"name": "Ali",  "timezone": "Asia/Karachi",     "hours": ["09:00", "17:00"], "country": "PK"},
    "sara@meetdesk.test": {"name": "Sara", "timezone": "Asia/Karachi",     "hours": ["09:00", "17:00"], "country": "PK"},
    "omar@meetdesk.test": {"name": "Omar", "timezone": "Asia/Karachi",     "hours": ["10:00", "18:00"], "country": "PK"},
    "zain@meetdesk.test": {"name": "Zain", "timezone": "Europe/London",    "hours": ["09:00", "17:00"], "country": "GB"},
    "hina@meetdesk.test": {"name": "Hina", "timezone": "America/New_York", "hours": ["09:00", "17:00"], "country": "US"},
}

# Mock holiday list for practice (fixed-date holidays only).
HOLIDAYS = {
    "PK": {"2026-03-23": "Pakistan Day", "2026-08-14": "Independence Day", "2026-12-25": "Quaid-e-Azam Day"},
    "GB": {"2026-12-25": "Christmas Day"},
    "US": {"2026-07-04": "Independence Day", "2026-12-25": "Christmas Day"},
}

@mcp.tool()
def find_person(query: str) -> list[dict]:
    """Find people by name or email fragment. Returns email, name, timezone and working hours."""
    q = query.lower()
    return [{"email": e, **p} for e, p in PEOPLE.items() if q in e or q in p["name"].lower()]

@mcp.tool()
def public_holidays(country: str, year: int) -> dict[str, str]:
    """Public holidays for a country code (PK, GB, US) in a year, as {date: name}."""
    return {d: n for d, n in HOLIDAYS.get(country.upper(), {}).items() if d.startswith(str(year))}

if __name__ == "__main__":
    mcp.run()