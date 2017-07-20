import logging
import os
import requests
import sys

from ..database import Database
from load_sprints import sprints_handler
from issue_changelogs import changelogs_handler

def main():
    sprint_info = {
        'rapidview_id': 219, 
        'sprints': [225, 226, 228, 229,]
    }

    rapidview = sprint_info['rapidview_id']
    sprints = sprint_info['sprints']

    for sprint in sprints:
        sprints_handler(
            {
                'rapidview_id': rapidview, 
                'sprint_id': sprint
            }
        )
        changelogs_handler(
            {
                'sprint_id': sprint
            }
        )
    
    database = Database()
    database.refresh_materialized_view("sprint_view")
  
if __name__== "__main__":
    main()
