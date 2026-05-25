# Suppevo MCP Power

Manage the Suppevo supplement-tracking platform directly from Kiro. Search products, track supplements, log doses, browse ingredients, manage brands, and more — all through natural language.

## Overview

This power connects to the [Suppevo API](https://api.dev.suppevo.com/) via an MCP server, providing 100+ tools for supplement tracking, product discovery, ingredient intelligence, and platform administration.

## Setup

### 1. Install dependencies

The power uses `uvx` to run the MCP server. Make sure you have `uv` installed:

```bash
# macOS
brew install uv

# Or via pip
pip install uv
```

### 2. Configure credentials

Add your Suppevo credentials to `~/.env`:

```bash
# Suppevo MCP Server
SUPPEVO_API_TOKEN=your-jwt-token-here
SUPPEVO_REFRESH_TOKEN=your-refresh-token-here
SUPPEVO_CLIENT_ID=your-cognito-client-id
SUPPEVO_API_BASE_URL=https://api.dev.suppevo.com/
SUPPEVO_COGNITO_REGION=us-east-1
```

**Getting your token:**
1. Sign in to the Suppevo app
2. Retrieve your JWT (IdToken) from the authenticated Cognito session
3. Copy the refresh token and client ID for automatic token renewal

The server auto-refreshes expired tokens if `SUPPEVO_REFRESH_TOKEN` and `SUPPEVO_CLIENT_ID` are provided.

### 3. MCP Server Configuration

```json
{
  "mcpServers": {
    "suppevo": {
      "command": "uvx",
      "args": ["suppevo-mcp"]
    }
  }
}
```

Or from source:

```json
{
  "mcpServers": {
    "suppevo": {
      "command": "python3",
      "args": ["-m", "suppevo_mcp"],
      "cwd": "/path/to/suppevo-data-mcp"
    }
  }
}
```

## Capabilities

### User Tools (authenticated)

| Tool Group | What you can do |
|------------|-----------------|
| **Profile** | Get/create/update your user profile and preferences |
| **Supplements** | Add, view, update, remove supplements from your tracking list |
| **Schedules** | Create dosing schedules with frequency, time-of-day, and reminders |
| **Doses** | Log doses, view history, get summaries over date ranges |
| **Reviews** | Write reviews for products and brands |
| **Rewards** | Check points balance, badges, streaks, and active challenges |
| **Stack Analysis** | Analyze your full supplement stack for overlaps, gaps, warnings, and recommendations |
| **Suggestions** | Submit data corrections or improvements |

### Discovery Tools (public, no auth needed)

| Tool Group | What you can do |
|------------|-----------------|
| **Product Search** | Search by name, category, brand, ingredient, UPC, or tag |
| **Brand Search** | Find brands by name, location, or text search |
| **Ingredient Search** | Browse and search the ingredient database |
| **Ingredient Intelligence** | Get alternatives, interactions, dosing guides, effectiveness data |
| **Benefits** | Browse health benefit categories and ranked ingredients |
| **Biomarkers** | View biomarker reference ranges and supporting ingredients |
| **News** | Browse the supplement industry news feed |
| **Scoring** | Get product ingredient scores and compare products |

### Admin Tools (admin token required)

| Tool Group | What you can do |
|------------|-----------------|
| **Products** | Create, update, delete, bulk operations |
| **Brands** | Create, update, delete brands |
| **Ingredients** | Create, update, delete, bulk ops, merge, auto-link |
| **Reviews** | Moderate (approve/reject/flag) |
| **News** | Create, update, delete news items |
| **Users** | List users, manage groups, assign brand ownership |
| **Benefits** | Create/update benefit categories, rebuild rankings |
| **Biomarkers** | Create, update, delete biomarkers |
| **Evidence Links** | Create, update, delete scientific evidence |
| **Suggestions** | Review and approve/reject user suggestions |
| **Exports** | Generate data exports |

## Example Prompts

**Supplement tracking:**
- "Show my current supplement stack"
- "Add Vitamin D 5000 IU to my supplements"
- "Log a dose of magnesium — 400mg taken this morning"
- "What's my current streak?"

**Product discovery:**
- "Search for magnesium glycinate supplements"
- "Compare these two products: [id1] vs [id2]"
- "What's the ingredient score for this product?"
- "Find products with ashwagandha"

**Ingredient intelligence:**
- "What are the interactions for Vitamin D?"
- "Show me the dosing guide for magnesium"
- "Compare magnesium glycinate vs magnesium citrate"
- "What are the top ingredients for sleep?"

**Stack analysis:**
- "Analyze my supplement stack for overlaps"
- "Are there any warnings in my current stack?"
- "What gaps do I have based on my health goals?"
- "Give me recommendations based on my stack"

**Admin operations:**
- "Create a new product called 'Omega-3 Fish Oil' in the heart category"
- "Bulk create these 10 ingredients"
- "Show the moderation queue"
- "Approve this review"

## Keywords

suppevo, supplements, vitamins, health, nutrition, tracking, doses, ingredients, products, brands, biomarkers, stack analysis, wellness, MCP

## Source

- **Repository:** https://github.com/GomezMera-IO-LLC/suppevo-data-mcp
- **PyPI:** https://pypi.org/project/suppevo-mcp/
- **License:** MIT
