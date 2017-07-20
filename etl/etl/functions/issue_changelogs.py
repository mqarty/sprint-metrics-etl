#!/usr/bin/env python
# -*- coding: utf-8 -*-

import base64
import grequests
import logging
import logging.handlers
import os
import requests
import sys

from ..database import Database

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


CHANGELOG_URI = "/rest/api/2/issue/{issue_key}?expand=changelog"

def _fetch_sprint_issue_url_to_issue_map(args):
    database = Database()

    results = database.fetchall(
        """SELECT 
            si.id, si.issue_key
           FROM 
            sprint_issues si JOIN
                sprints s ON
            si.sprint_id = s.id
           WHERE
            s.sprint_jid = {sprint_id}""".format(**args)
        )

    urls = {}
    for result in results:
        issue_id = result[0]
        jira_key = result[1]

        urls[os.environ['JIRA_URI']+CHANGELOG_URI.format(issue_key=jira_key)] = issue_id

    return urls

def _process_all_urls(urls):
    database = Database()

    credentials = "{}:{}".format(os.environ['USERNAME'], os.environ['PASSWORD'])
    auth = base64.b64encode(credentials)

    header = {"Authorization": "Basic {}".format(auth)}

    rs = (grequests.get(u, headers=header) for u in urls)
    
    results = grequests.map(rs)

    for r in results:
        if not r:
            #TODO: why is it returning None
            logger.error("Request is NONE...{}".format(r))
            continue

        if r.status_code == requests.codes.ok:
            issue_data = r.json()
            issue_id = urls[r.url]
            changelog = issue_data['changelog']
            start = changelog['startAt']
            max_results = changelog['maxResults']
            total = changelog['total']

            if max_results < total:
                raise Exception("Need to implement")

            changelogs = issue_data['changelog']['histories']
            for changelog in changelogs:
                history_jid = changelog.pop('id', None)
                items = changelog.pop('items', None)
                changelog_pk = database.upsert_issue_changelog(issue_id, history_jid, changelog)

                for item in items:
                    database.upsert_changelog_item(changelog_pk, item)
        else:
            logger.exception(r.url)
        
        urls.pop(r.url, None)

    return urls
    
def changelogs_handler(args):

    assert "sprint_id" in args

    urls = _fetch_sprint_issue_url_to_issue_map(args)

    remaining_urls = _process_all_urls(urls)

    #Basic Retry
    remaining_urls = _process_all_urls(remaining_urls)

    logger.info("-----------------Remaining URLs :: {}".format(remaining_urls))
