import os
import requests
import re

# Read secrets from environment variables (set these in Actions or locally)
TOKEN = os.getenv("GH_TOKEN")
PROJECT_ID = os.getenv("PROJECT_ID")

if not TOKEN or not PROJECT_ID:
    raise SystemExit("Missing GH_TOKEN or PROJECT_ID environment variable")

# GraphQL query: get up to 100 items from the Project
query = """
query($id:ID!) {
  node(id: $id) {
    ... on ProjectV2 {
      items(first: 100) {
        nodes {
          content {
            ... on Issue {
              state
            }
            ... on PullRequest {
              state
            }
          }
        }
      }
    }
  }
}
"""

headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Accept": "application/vnd.github.v3+json"
}

resp = requests.post(
    "https://api.github.com/graphql",
    json={"query": query, "variables": {"id": PROJECT_ID}},
    headers=headers,
)
resp.raise_for_status()
data = resp.json()

# Navigate the JSON safely
items = data.get("data", {}).get("node", {}).get("items", {}).get("nodes", []) or []

done = sum(
    1
    for i in items
    if i.get("content") and i["content"].get("state") == "CLOSED"
)
total = len(items)
progress = int((done / total) * 100) if total > 0 else 0

# Make a visual bar of 10 blocks
bars = 10
filled = int(progress / 100 * bars)
progress_bar = "█" * filled + "░" * (bars - filled)

progress_text = (
    "<!-- PROJECT_PROGRESS_START -->\n"
    f"✅ {done} / {total} tasks completed ({progress}%)\n"
    f"[{progress_bar}] {progress}%\n"
    "<!-- PROJECT_PROGRESS_END -->"
)

# Replace in README
with open("README.md", "r", encoding="utf-8") as f:
    readme = f.read()

new_readme = re.sub(
    r"<!-- PROJECT_PROGRESS_START -->.*<!-- PROJECT_PROGRESS_END -->",
    progress_text,
    readme,
    flags=re.DOTALL,
)

with open("README.md", "w", encoding="utf-8") as f:
    f.write(new_readme)

print("README updated:", f"{done}/{total} ({progress}%)")
