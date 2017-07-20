import logging
import logging.handlers
import os
import requests
import sys

from ..database import Database

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def sprints_handler(args):

    assert "rapidview_id" in args
    assert "sprint_id" in args

    database = Database()

    r = requests.get(
        os.environ['JIRA_URI']+'/rest/greenhopper/1.0/rapid/charts/sprintreport?rapidViewId={rapidview_id}&sprintId={sprint_id}'.format(**args), 
        auth=(
            os.environ['USERNAME'], 
            os.environ['PASSWORD']
        )
    )

    logger.info("Request Status {}".format(r.status_code))

    if r.status_code == requests.codes.ok:
        sprint_data = r.json()
        sprint = sprint_data['sprint']
        contents = sprint_data['contents']

        sprint_id = sprint['id']
        jdoc = {
            "name": sprint['name'],
            "state": sprint['state'],
            "goal": sprint['goal'],
            "completed_date": sprint['completeDate'],
            "days_remaining": sprint['daysRemaining'],
            "all_issues_estimate_sum": contents['allIssuesEstimateSum'],
            "completed_issues_initial_estimate_sum": contents['completedIssuesInitialEstimateSum'],
            "completed_issues_estimate_sum": contents['completedIssuesEstimateSum'],
            "punted_issues_initial_estimate_sum": contents['puntedIssuesInitialEstimateSum'],
            "punted_issues_estimate_sum": contents['puntedIssuesEstimateSum'],
            "issues_completed_in_another_sprint_initial_estimate_sum": contents['issuesCompletedInAnotherSprintInitialEstimateSum'],
            "issues_completed_in_another_sprint_estimate_sum": contents['issuesCompletedInAnotherSprintEstimateSum'],
            "issues_not_completed_initial_estimate_sum": contents['issuesNotCompletedInitialEstimateSum'],
            "issues_not_completed_initial_estimate_sum": contents['issuesNotCompletedEstimateSum']
        }
        sprint_pk = database.upsert_sprint(sprint_id, jdoc, sprint['startDate'], sprint['endDate'])

        added_during_sprint = contents['issueKeysAddedDuringSprint']
        for item in contents['completedIssues']:
            logger.info("Completed Issues: {}".format(item))
            issue_id = item.pop('id', None)
            issue_key = item.pop('key', None)
            database.upsert_issue(sprint_pk, issue_id, issue_key, item, completed=True, added_during_sprint=issue_key in added_during_sprint)
        
        for item in contents['puntedIssues']:
            logger.info("Punted Issues: {}".format(item))
            issue_id = item.pop('id', None)
            issue_key = item.pop('key', None)
            database.upsert_issue(sprint_pk, issue_id, issue_key, item, punted=True, added_during_sprint=issue_key in added_during_sprint)

        for item in contents['issuesCompletedInAnotherSprint']:
            logger.info("Issues Completed in Another Sprint: {}".format(item))
            issue_id = item.pop('id', None)
            issue_key = item.pop('key', None)
            database.upsert_issue(sprint_pk, issue_id, issue_key, item, completed_in_another_sprint=True, added_during_sprint=issue_key in added_during_sprint)

        for item in contents['issuesNotCompletedInCurrentSprint']:
            logger.info("Issues Not Completed in Current Sprint: {}".format(item))
            issue_id = item.pop('id', None)
            issue_key = item.pop('key', None)
            database.upsert_issue(sprint_pk, issue_id, issue_key, item, not_completed_in_current_sprint=True, added_during_sprint=issue_key in added_during_sprint)
    else:
        logger.exception(r.url)
  