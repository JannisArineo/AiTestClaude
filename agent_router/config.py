"""
Agent Routing System — Configuration
"""

# ─────────────────────────────────────────────
# Model IDs
# ─────────────────────────────────────────────
ROUTER_MODEL = "claude-haiku-4-5"       # Fast, cheap classifier
EXPENSIVE_MODEL = "claude-opus-4-6"     # Full reasoning power
CHEAP_MODEL = "claude-haiku-4-5"        # Fast + tools / skills

# ─────────────────────────────────────────────
# Routing thresholds
# ─────────────────────────────────────────────
# Complexity 1-10 assigned by the router.
# >= EXPENSIVE_THRESHOLD  → expensive model
# tool_needed == true     → cheap model + MCP tools
# else                    → cheap model + skills
EXPENSIVE_THRESHOLD = 7

# ─────────────────────────────────────────────
# Token budgets
# ─────────────────────────────────────────────
ROUTER_MAX_TOKENS = 512        # Only needs to return JSON
EXPENSIVE_MAX_TOKENS = 8192
CHEAP_MAX_TOKENS = 4096

# ─────────────────────────────────────────────
# Route names (used as keys throughout the system)
# ─────────────────────────────────────────────
ROUTE_EXPENSIVE = "expensive"
ROUTE_CHEAP_MCP = "cheap_mcp"
ROUTE_CHEAP_SKILLS = "cheap_skills"
