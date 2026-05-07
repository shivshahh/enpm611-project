# ============================================================================
# issue_pull.py
# Pulls all issues and timeline events from python-poetry/poetry via GitHub
# GraphQL API and saves them to poetry_issues.json
#
# Uses cursor-based pagination to fetch 100 issues per request
# Each issue includes up to 100 timeline events in same request
# Supports resuming from existing data so re-runs only fetch new issues
#
# Output format (poetry_issues.json):
#   [
#     {
#       "url"          : "https://github.com/python-poetry/poetry/issues/123"
#       "creator"      : "username"
#       "labels"       : ["bug", "triage"]
#       "state"        : "open" or "closed"
#       "assignees"    : ["username1", "username2"]
#       "title"        : "Issue title"
#       "text"         : "Issue body text"
#       "number"       : 123
#       "created_date" : "2024-01-01T00:00:00Z"
#       "updated_date" : "2024-01-02T00:00:00Z"
#       "timeline_url" : "https://api.github.com/repos/.../timeline"
#       "events"       : [{ "event_type", "author", "event_date", "comment" }]
#     }
#   ]
#
# Prerequisites:
#   pip install requests python-dotenv
#   Create .env file with GITHUB_TOKEN=your_token
# ============================================================================

import requests
import json
import os
import time
from dotenv import load_dotenv

# Load environment variables from .env file in project root
load_dotenv()

# ============================================================================
# GitHub Token Setup
# ============================================================================
#  1 - Go to https://github.com/settings/tokens
#  2 - Click "Generate new token (classic)"
#  3 - Give token a name (eg "enpm611-project")
#  4 - Select "repo" scope for access to public repo data
#  5 - Click Generate token and copy it to .env as GITHUB_TOKEN=your_token

# ============================================================================
# API Configuration
# ============================================================================

# GitHub GraphQL endpoint - single endpoint for all queries
GRAPHQL_URL = "https://api.github.com/graphql"

# Auth header required for all GitHub API requests
headers = {
    "Authorization": f"Bearer {os.environ['GITHUB_TOKEN']}",
}

# Session reuses TCP connections across requests for better performance
session = requests.Session()
session.headers.update(headers)

# ============================================================================
# GraphQL Query
# ============================================================================
# Fetches 100 issues per request ordered by creation date (newest first)
# Each issue includes:
#   - Basic fields: number, title, body, state, dates, url
#   - Author login name
#   - Up to 10 assignees
#   - Up to 20 labels
#   - Up to 100 timeline events of these types:
#       IssueComment      - comment left on issue
#       ClosedEvent       - issue was closed
#       ReopenedEvent     - issue was reopened
#       LabeledEvent      - label was added
#       AssignedEvent     - someone was assigned
#       ReferencedEvent   - issue was referenced from a commit or PR
#       CrossReferencedEvent - issue was mentioned in another issue or PR
#
# Pagination uses cursor-based approach:
#   - First request sends cursor=None to start from beginning
#   - Each response includes endCursor to pass as next request cursor
#   - hasNextPage indicates if more results exist

QUERY = """
query($cursor: String) {
  repository(owner: "python-poetry", name: "poetry") {
    issues(first: 100, after: $cursor, orderBy: {field: CREATED_AT, direction: DESC}) {
      pageInfo {
        hasNextPage
        endCursor
      }
      nodes {
        number
        title
        body
        state
        createdAt
        updatedAt
        url
        author { login }
        assignees(first: 10) { nodes { login } }
        labels(first: 20) { nodes { name } }
        timelineItems(first: 100) {
          nodes {
            __typename
            ... on IssueComment {
              body
              author { login }
              createdAt
            }
            ... on ClosedEvent {
              actor { login }
              createdAt
            }
            ... on ReopenedEvent {
              actor { login }
              createdAt
            }
            ... on LabeledEvent {
              label { name }
              actor { login }
              createdAt
            }
            ... on AssignedEvent {
              assignee { ... on User { login } }
              actor { login }
              createdAt
            }
            ... on ReferencedEvent {
              actor { login }
              createdAt
            }
            ... on CrossReferencedEvent {
              actor { login }
              createdAt
            }
          }
        }
      }
    }
  }
}
"""

# ============================================================================
# Resume Support
# ============================================================================
# Load previously collected issues from poetry_issues.json if it exists
# Build a set of issue numbers already collected so we can skip them
# This allows re-running script to pick up where it left off
existing_numbers = set()
try:
    with open("Poetry.json", "r") as f:
        cleaned = json.load(f)
    existing_numbers = {issue["number"] for issue in cleaned}
    print(f"Loaded {len(cleaned)} existing issues (highest #{max(existing_numbers)})")
except (FileNotFoundError, json.JSONDecodeError):
    cleaned = []
    print("No existing data found, starting fresh")

# ============================================================================
# Main Collection Loop
# ============================================================================
# Cursor tracks pagination position - None means start from beginning
cursor = None
page   = 1

while True:
    # Send GraphQL query with current cursor position
    response = session.post(GRAPHQL_URL, json={"query": QUERY, "variables": {"cursor": cursor}})

    # Rate limit handling - GitHub returns 403 or 429 when limit exceeded
    # Retry-After header tells us how long to wait in seconds
    if response.status_code in (403, 429):
        retry_after = int(response.headers.get("Retry-After", 60))
        print(f"  Rate limited, waiting {retry_after}s...")
        time.sleep(retry_after)
        continue  # Retry same page

    # Any other non-200 response is an unexpected error
    if response.status_code != 200:
        print(f"Got response code: {response.status_code}, expected 200")
        break

    data = response.json()

    # GraphQL can return 200 with errors in response body
    if "errors" in data:
        print(f"GraphQL errors: {data['errors']}")
        break

    # Extract pagination info and issue nodes from response
    issues_data = data["data"]["repository"]["issues"]
    page_info   = issues_data["pageInfo"]
    nodes       = issues_data["nodes"]

    new_count = sum(1 for n in nodes if n["number"] not in existing_numbers)
    print(f"Page {page}: {len(nodes)} issues ({new_count} new)")

    # Process each issue on this page
    for issue in nodes:
        # Skip issues we already have from previous runs
        if issue["number"] in existing_numbers:
            continue

        # Build issue dict matching expected output format
        # Fields mapped from GraphQL response to flat JSON structure
        issue_json = {
            "url"          : issue["url"],
            "creator"      : issue["author"]["login"] if issue["author"] else "",
            "labels"       : [label["name"] for label in issue["labels"]["nodes"]],
            "state"        : issue["state"].lower(),
            "assignees"    : [a["login"] for a in issue["assignees"]["nodes"]],
            "title"        : issue["title"],
            "text"         : issue["body"].replace("\r", "") if issue["body"] else "",
            "number"       : issue["number"],
            "created_date" : issue["createdAt"],
            "updated_date" : issue["updatedAt"],
            "timeline_url" : f"https://api.github.com/repos/python-poetry/poetry/issues/{issue['number']}/timeline",
            "events"       : [],
        }

        # Extract timeline events from same GraphQL response
        # No extra API call needed - events come bundled with each issue
        for event in issue["timelineItems"]["nodes"]:
            event_type = event.get("__typename", "")

            # IssueComment events have body text and author login
            if event_type == "IssueComment":
                issue_json["events"].append({
                    "event_type" : "commented",
                    "author"     : event["author"]["login"] if event.get("author") else "",
                    "event_date" : event.get("createdAt", ""),
                    "comment"    : event.get("body", ""),
                })
            # All other tracked event types share same structure: actor + date
            elif event_type in ("ClosedEvent", "ReopenedEvent", "LabeledEvent",
                                "AssignedEvent", "ReferencedEvent", "CrossReferencedEvent"):
                issue_json["events"].append({
                    "event_type" : event_type,
                    "author"     : event["actor"]["login"] if event.get("actor") else "",
                    "event_date" : event.get("createdAt", ""),
                    "comment"    : "",
                })

        cleaned.append(issue_json)

    # Save after each page so progress survives crashes or interrupts
    with open("Poetry.json", "w") as output:
        json.dump(cleaned, output, indent=2)

    # Check if more pages exist - if not we collected everything
    if not page_info["hasNextPage"]:
        break

    # Advance cursor to next page position
    cursor = page_info["endCursor"]
    page += 1

print(f"Done. Total issues: {len(cleaned)}")
