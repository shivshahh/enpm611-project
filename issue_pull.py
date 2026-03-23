import requests
import json

url = 'https://api.github.com/repos/python-poetry/poetry/issues'
payload = {
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2026-03-10",
}

response = requests.get(url, data=payload)
cleaned = []

if response.status_code == 200:
    for issue in response.json():
        issue_json = {}
        
        # Copied field gets from project outline
        issue_json["url"] = issue["html_url"]
        issue_json["creator"] = issue["user"]["login"]
        issue_json["labels"] = [label["name"] for label in issue["labels"]]
        issue_json["state"] = issue["state"]
        issue_json["assignees"] = [assignee["login"] for assignee in issue["assignees"]]
        issue_json["title"] = issue["title"]
        issue_json["text"] = issue["body"].replace("\r", "")
        issue_json["number"] = issue["number"]
        issue_json["created_date"] = issue["created_at"]
        issue_json["updated_date"] = issue["updated_at"]
        issue_json["timeline_url"] = f"https://api.github.com/repos/python-poetry/poetry/issues/{issue["number"]}/timeline"
        issue_json["events"] = []

        timeline_response = requests.get(issue_json["timeline_url"], data=payload)
        for event in timeline_response.json():
            event_json = {}
            event_json["event_type"] = event["event"]

            # If there's no author it's probably a bot issue and we want to ignore those
            try :
                event_json["author"] = event["author"]["name"]
                event_json["event_date"] = event["author"]["date"]
                event_json["comment"] = event["message"] 
            except KeyError:
                continue
            
            issue_json["events"].append(event_json)

        cleaned.append(issue_json)

    with open("poetry_issues.json", "w") as output:
        json.dump(cleaned, output, indent=2)

else:
    print("Got response code: " + str(response.status_code) + " expected 200")