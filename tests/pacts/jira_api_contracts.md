# Pact CDC Contracts -- mcp-jira-api Gap Closure

Consumer: mcp-jira-api (MCP server tool layer)
Provider: Jira REST API (Core v2/v3) + Jira Agile REST API (1.0)

Each interaction documents the request shape sent by the tool and the response
shape the tool relies on. URL templates omit the base (cfg["url"]) and version
segment (cfg["api_version"]) for Core API, shown as /rest/api/{ver}/...

---

## Gap 2 -- Epic Management

### jira_create_epic
- Interaction: "create an epic"
- Request:
  - Method: POST
  - Path: /rest/api/{ver}/issue
  - Body: {"fields": {"project": {"key": "<project_key>"}, "issuetype": {"name": "Epic"}, "summary": "<summary>", "customfield_10014": "<name>", "duedate"?: "<due_date>", "customfield_10015"?: "<start_date>"}}
- Response (200/201):
  - {"id": "<id>", "key": "<KEY>"}
- Tool consumes: result["key"], result["id"]

### jira_get_epic
- Interaction: "fetch epic detail then its linked stories"
- Request 1:
  - Method: GET
  - Path: /rest/api/{ver}/issue/<epic_key>?fields=summary,status,customfield_10014,customfield_10016
- Response 1: {"fields": {"summary": "<s>", "status": {"name": "<st>"}, "customfield_10014": "<name>"}}
- Request 2:
  - Method: GET
  - Path: /rest/api/{ver}/search?jql=<encoded "Epic Link"="<key>" | cf[10014]=<key>>&fields=summary,status,customfield_10016,customfield_10028,story_points&maxResults=100
- Response 2: {"issues": [{"fields": {"status": {"name": "Done"}, "customfield_10016": 5.0}}], "total": N}
- Tool consumes: issues[].fields.status.name, story points via _extract_story_points

### jira_link_to_epic
- Interaction: "set the epic link field on an issue"
- Request:
  - Method: PUT
  - Path: /rest/api/{ver}/issue/<issue_key>
  - Body: {"fields": {"customfield_10014": "<epic_key>"}}
- Response (204): empty body
- Tool consumes: nothing from body; success implied by no exception

### jira_list_epics
- Interaction: "list epics on a board"
- Request:
  - Method: GET
  - Path: /rest/agile/1.0/board/<board_id>/epic
- Response (200): {"values": [{"key": "<KEY>", "summary": "<s>", "done": false}], "total": N}
- Tool consumes: values[].key, values[].summary, values[].done

---

## Gap 3 -- Release & Version Management

### jira_create_version
- Interaction: "create a project version"
- Request:
  - Method: POST
  - Path: /rest/api/{ver}/version
  - Body: {"project": "<project_key>", "name": "<name>", "released": false, "archived": false, "releaseDate"?: "<date>", "description"?: "<desc>"}
- Response (201): {"id": "<id>", "name": "<name>"}
- Tool consumes: result["id"], result["name"]

### jira_list_versions
- Interaction: "list versions for a project"
- Request:
  - Method: GET
  - Path: /rest/api/{ver}/project/<project_key>/versions
- Response (200): [{"id": "<id>", "name": "<name>", "released": bool, "archived": bool, "releaseDate": "<date>|null"}]
- Tool consumes: each element's id, name, released, archived, releaseDate

### jira_release_version
- Interaction: "mark a version released"
- Request:
  - Method: PUT
  - Path: /rest/api/{ver}/version/<version_id>
  - Body: {"released": true, "releaseDate": "<date|today>"}
- Response (200): {"id": "<id>", "released": true}
- Tool consumes: nothing from body; success implied by no exception

### jira_release_notes
- Interaction: "search issues fixed in a version, grouped by type"
- Request:
  - Method: GET
  - Path: /rest/api/{ver}/search?jql=<encoded project="<key>" AND fixVersion="<sanitized name>" ORDER BY issuetype ASC>&fields=summary,issuetype,status&maxResults=100
  - Security: version_name double-quotes escaped (\") before JQL build to prevent injection
- Response (200): {"issues": [{"key": "<K>", "fields": {"summary": "<s>", "issuetype": {"name": "Bug"}, "status": {"name": "Done"}}}], "total": N}
- Tool consumes: issues[].fields.issuetype.name (grouping key), summary, status.name

---

## Gap 4 -- Cross-Board / Multi-Team Metrics

### jira_program_velocity (per board in board_ids)
- Interaction: "fetch velocity chart for a board"
- Request:
  - Method: GET
  - Path: /rest/agile/1.0/rapid/charts/velocity?rapidViewId=<board_id>
- Response (200): {"velocityStatEntries": {"<sprintId>": {"completed": {"value": N}, "estimated": {"value": N}}}}
- Tool consumes: velocityStatEntries[*].completed.value

### jira_cross_team_health (per board in board_ids)
- Interaction: "fetch closed sprints, then issues per sprint"
- Request 1:
  - Method: GET
  - Path: /rest/agile/1.0/board/<board_id>/sprint?state=closed&maxResults=6
- Response 1: {"values": [{"id": <sprintId>}]}
- Request 2 (per sprint):
  - Method: GET
  - Path: /rest/agile/1.0/sprint/<sprintId>/issue?maxResults=200&fields=status,customfield_10016,customfield_10028,story_points
- Response 2: {"issues": [{"fields": {"status": {"name": "Done"}, "customfield_10016": 5.0}}]}
- Tool consumes: done-state issue story points to build velocity history

### jira_dependency_check (per board in board_ids)
- Interaction: "fetch active sprint, its issues, then each issue's links"
- Request 1:
  - Method: GET
  - Path: /rest/agile/1.0/board/<board_id>/sprint?state=active
- Response 1: {"values": [{"id": <sprintId>}]}
- Request 2:
  - Method: GET
  - Path: /rest/agile/1.0/sprint/<sprintId>/issue?maxResults=200&fields=summary,issuelinks
- Response 2: {"issues": [{"key": "<K>"}]}
- Request 3 (per issue):
  - Method: GET
  - Path: /rest/api/{ver}/issue/<issue_key>?fields=issuelinks
- Response 3: {"fields": {"issuelinks": [{"type": {"name": "Blocks"}, "outwardIssue": {"key": "<OTHER>"}}]}}
- Tool consumes: issuelinks[].type.name == "Blocks", outwardIssue.key (matched against board_issue_map)

---

## Notes

- All tools authenticate via Authorization header (Basic or Bearer) built in
  server._build_auth_header / agile_client._build_agile_auth_header.
- On any non-2xx, the provider returns {"errorMessages": [...], "errors": {...}};
  the consumer surfaces this as {"success": false, "error": "Jira API error <code>: <detail>"}.
- customfield_10014 (Epic Link/Name) and customfield_10016 (Story Points) are
  Cloud defaults; Server/Data Center instances may use different custom field IDs
  (see blueprint risk register R-01, R-02).
