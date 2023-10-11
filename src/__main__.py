import argparse
import datetime
import os
from github import Auth, PullRequest, Github, Repository
import smartsheet


def env_opts(env: str):
    if env in os.environ:
        return {'default': os.environ[env]}
    else:
        return {'required': True}

def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Create a Jira Issue from a GitHub tag release."
    )

    parser.add_argument("--dry_run", dest="dry_run",
                        action="store",
                        help="Use this flag to run the program in dry-run mode, means it will not create any Jiras", required=False, default="true")


    parser.add_argument("--gh_token", dest="gh_token",
                        help="", **env_opts("GITHUB_TOKEN"))

    parser.add_argument("--ss_token", dest="ss_token",
                        help="", **env_opts("SMARTSHEET_ACCESS_TOKEN"))

    args = parser.parse_args()

    return args

def extract_issues_with_filter_labels(gh:Github, filter_label):
    issues = []
    upstream_orgs = ['opendatahub-io']
    numberOfDaysToFetchTheIssuesFor = 7
    for upstream_org in upstream_orgs:
        issues += gh.search_issues(query=f'is:issue user:{upstream_org} label:{filter_label} updated:>{(datetime.datetime.now() - datetime.timedelta(days=numberOfDaysToFetchTheIssuesFor)).strftime("%Y-%m-%d")}')
    return issues

def update_issues_to_smartsheet(issues:list):
    column_map = {}
    smart = smartsheet.Smartsheet()
    # response = smart.Sheets.list_sheets()
    sheed_id = 7554346661138308
    sheet = smart.Sheets.get_sheet(sheed_id)
    for column in sheet.columns:
        column_map[column.title] = column.id
    print(column_map)
    issues_map = {issue.html_url:issue for issue in issues}
    rowsToAdd = []
    result = []
    existingRows = {row.cells[1].value:row for row in sheet.rows}
    rowsToUpdate = []

    for issue in issues:
        if issue.html_url not in existingRows:
            new_row = smart.models.Row()
            new_cell = smart.models.Cell()
            new_cell.column_id = column_map["Issue Title"]
            new_cell.value = issue.title
            new_row.cells.append(new_cell)

            new_cell = smart.models.Cell()
            new_cell.column_id = column_map["Issue link"]
            new_cell.value = issue.html_url
            new_row.cells.append(new_cell)

            new_cell = smart.models.Cell()
            new_cell.column_id = column_map["Created On"]
            new_cell.value = issue.created_at.strftime('%Y-%m-%dT%H:%M:%SZ')
            # '2023-10-10T00:00:00Z'
            new_row.cells.append(new_cell)

            new_cell = smart.models.Cell()
            new_cell.column_id = column_map["Status"]
            new_cell.value = issue.state
            new_row.cells.append(new_cell)

            new_cell = smart.models.Cell()
            new_cell.column_id = column_map["Closed On"]
            new_cell.value = issue.closed_at.strftime('%Y-%m-%dT%H:%M:%SZ') if issue.closed_at else ''
            new_row.cells.append(new_cell)

            new_row.to_bottom = True
            rowsToAdd.append(new_row)
        else:
            row = existingRows[issue.html_url]
            new_row = smart.models.Row()
            new_row.id = row.id

            new_cell = smart.models.Cell()
            new_cell.column_id = column_map["Issue Title"]
            new_cell.value = issue.title
            new_row.cells.append(new_cell)

            new_cell = smart.models.Cell()
            new_cell.column_id = column_map["Status"]
            new_cell.value = issue.state
            new_row.cells.append(new_cell)

            new_cell = smart.models.Cell()
            new_cell.column_id = column_map["Closed On"]
            new_cell.value = issue.closed_at.strftime('%Y-%m-%dT%H:%M:%SZ') if issue.closed_at else ''
            new_row.cells.append(new_cell)

            rowsToUpdate.append(new_row)

    #
    print(rowsToAdd)
    print(rowsToUpdate)
    if rowsToAdd:
        result.append(sheet.add_rows(rowsToAdd))
    if rowsToUpdate:
        result.append(smart.Sheets.update_rows(sheed_id, rowsToUpdate))
    return result
def main():
    args = parse_arguments()
    auth = Auth.Token(args.gh_token)
    gh = Github(auth=auth)
    args.dry_run = False if args.dry_run == "false" else True
    issues = extract_issues_with_filter_labels(gh, 'field-priority')
    result = update_issues_to_smartsheet(issues)
    print(result)

if __name__ == "__main__":
    main()