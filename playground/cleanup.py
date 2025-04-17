from linear_api.issue_manipulation import get_team_issues, delete_issue

team_name = "Test"
issues = get_team_issues(team_name)
for issue_id, title in issues.items():
    print(f"Deleting issue: {title} (ID: {issue_id})")
    delete_issue(issue_id)
