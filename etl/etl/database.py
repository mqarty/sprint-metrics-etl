#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import psycopg2

from datetime import datetime
from psycopg2 import IntegrityError


class Database(object):
    """
    Imperfect database abstraction
    """
    def get_connection(self):
        conn_string = "host='{0}' dbname='{1}' user='{2}'".format(
            'db', 'docker', 'docker')
        #if config.DB_PASS:
        conn_string = "{0} password={1}".format(conn_string, 'docker')
        # if a connection cannot be made an exception will be raised here
        return psycopg2.connect(conn_string)

    def fetchall(self, sql):
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(sql)
                return cursor.fetchall()

    def execute(self, sql, return_id=False):
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(sql)
                if return_id:
                    return cursor.fetchone()

    def _inclusive_tstzrange(self, start, end, interval=None, all_day=False):
        if end:
            end = "'{0}'::timestamptz".format(end.isoformat())
        if all_day:
            interval = '24 hour'
            start = start.replace(hour=0, minute=0, second=0)
        if interval:
            end = "'{start}'::timestamptz + '{interval}'::interval".format(
                start=start.isoformat(),
                interval=interval)
        return "tstzrange('{start}'::timestamptz, {end}, '[]')".format(
            start=start.isoformat(),
            end=end)

    def _get_returning_id(self):
         return "RETURNING id"

    def _get_insert_statment(self):
        return "INSERT INTO sprints(sprint_jid, jdoc, duration)"
    
    def _get_instance_values_statement(self, sprint_jid, jdoc, duration):
        return "VALUES ({sprint_jid}, $jdoc${jdoc}$jdoc$::jsonb, {duration})".format(
            sprint_jid=sprint_jid,
            jdoc=json.dumps(jdoc),
            duration=duration)
    
    def _get_conflict_statement(self, jdoc, duration):
        return """
                ON CONFLICT (sprint_jid) DO UPDATE SET
                    jdoc=$jdoc${jdoc}$jdoc$::jsonb,
                    duration={duration}""".format(
                    jdoc=json.dumps(jdoc),
                    duration=duration
                )

    def _get_issue_insert_statment(self):
        return "INSERT INTO sprint_issues(sprint_id, issue_jid, issue_key, jdoc, added_during_sprint, completed, punted, completed_in_another_sprint, not_completed_in_current_sprint)"
    
    def _get_issue_instance_values_statement(self, sprint_id, issue_jid, issue_key, jdoc, added_during_sprint=False, completed=False, punted=False, completed_in_another_sprint=False, not_completed_in_current_sprint=False):
        return "VALUES ({sprint_id}, {issue_jid}, '{issue_key}', $jdoc${jdoc}$jdoc$::jsonb, {added_during_sprint}, {completed}, {punted}, {completed_in_another_sprint}, {not_completed_in_current_sprint})".format(
            sprint_id=sprint_id,
            issue_jid=issue_jid,
            issue_key=issue_key,
            jdoc=json.dumps(jdoc),
            added_during_sprint=added_during_sprint, 
            completed=completed, 
            punted=punted, 
            completed_in_another_sprint=completed_in_another_sprint, 
            not_completed_in_current_sprint=not_completed_in_current_sprint)
    
    def _get_issue_conflict_statement(self, jdoc, added_during_sprint=False, completed=False, punted=False, completed_in_another_sprint=False, not_completed_in_current_sprint=False):
        return """
                ON CONFLICT (sprint_id, issue_jid, issue_key) DO UPDATE SET
                    jdoc=$jdoc${jdoc}$jdoc$::jsonb,
                    added_during_sprint={added_during_sprint}, 
                    completed={completed}, 
                    punted={punted}, 
                    completed_in_another_sprint={completed_in_another_sprint}, 
                    not_completed_in_current_sprint={not_completed_in_current_sprint}""".format(
                    jdoc=json.dumps(jdoc),
                    added_during_sprint=added_during_sprint, 
                    completed=completed, 
                    punted=punted, 
                    completed_in_another_sprint=completed_in_another_sprint, 
                    not_completed_in_current_sprint=not_completed_in_current_sprint)

    def _get_issue_changelog_insert_statment(self):
        return "INSERT INTO issue_changelogs(issue_id, history_jid, jdoc)"
    
    def _get_issue_changelog_instance_values_statement(self, issue_id, history_jid, jdoc):
        return "VALUES ({issue_id}, {history_jid}, $jdoc${jdoc}$jdoc$::jsonb)".format(
            issue_id=issue_id,
            history_jid=history_jid,
            jdoc=json.dumps(jdoc))
    
    def _get_issue_changelog_conflict_statement(self, issue_id, history_jid, jdoc):
        return """
                ON CONFLICT (issue_id, history_jid) DO UPDATE SET
                    jdoc=$jdoc${jdoc}$jdoc$::jsonb""".format(
                    jdoc=json.dumps(jdoc))

    def _get_changelog_item_insert_statment(self):
        return "INSERT INTO changelog_items(changelog_id, field, field_type, field_id, from_id, from_string, to_id, to_string)"
    
    def _get_changelog_item_instance_values_statement(self, changelog_id, **item):
        return """VALUES ({changelog_id}, '{field}', '{field_type}', '{field_id}', '{from_id}', $from${from_string}$from$::text, '{to_id}', $to${to_string}$to$::text)""".format(
            changelog_id=changelog_id,
            field=item.get('field'),
            field_type=item.get('fieldtype'),
            field_id=item.get('fieldId'),
            from_id=item.get('from'),
            from_string=None if item.get('fromString') is None else item.get('fromString').encode('utf-8'),
            to_id=item.get('to'),
            to_string=None if item.get('toString') is None else item.get('toString').encode('utf-8')
            )

    def _get_changelog_item_conflict_statement(self, **item):
        return """
                ON CONFLICT (changelog_id, to_id, from_id) DO UPDATE SET
                    from_string=$from${from_string}$from$,
                    to_string=$to${to_string}$to$""".format(
                    from_string=None if item.get('fromString') is None else item.get('fromString').encode('utf-8'),
                    to_string=None if item.get('toString') is None else item.get('toString').encode('utf-8')
                    )

    def upsert_sprint(self, sprint_id, jdoc, start, end):
        start = datetime.strptime(start, '%d/%b/%y %H:%M %p')
        end = datetime.strptime(end, '%d/%b/%y %H:%M %p')
        duration = self._inclusive_tstzrange(
            start, end,
            all_day=jdoc.get('all_day', False))

        sql = "{insert_statment}\n{values_statement}\n{conflict_statement}\n{returning_id};".format(
            insert_statment=self._get_insert_statment(),
            values_statement=self._get_instance_values_statement(
                sprint_id, jdoc, duration),
            conflict_statement=self._get_conflict_statement(
                jdoc, duration),
            returning_id=self._get_returning_id())

        result = self.execute(sql, return_id=True)
        return result[0]

    def upsert_issue(self, sprint_id, issue_id, issue_key, jdoc, added_during_sprint=False, completed=False, punted=False, completed_in_another_sprint=False, not_completed_in_current_sprint=False):
        sql = "{insert_statment}\n{values_statement}\n{conflict_statement};".format(
            insert_statment=self._get_issue_insert_statment(),
            values_statement=self._get_issue_instance_values_statement(
                sprint_id, issue_id, issue_key, jdoc, added_during_sprint, completed, punted, completed_in_another_sprint, not_completed_in_current_sprint),
            conflict_statement=self._get_issue_conflict_statement(
                jdoc, added_during_sprint, completed, punted, completed_in_another_sprint, not_completed_in_current_sprint))

        self.execute(sql)

    def upsert_issue_changelog(self, issue_id, history_jid, jdoc):
        sql = "{insert_statment}\n{values_statement}\n{conflict_statement}\n{returning_id};".format(
            insert_statment=self._get_issue_changelog_insert_statment(),
            values_statement=self._get_issue_changelog_instance_values_statement(issue_id, history_jid, jdoc),
            conflict_statement=self._get_issue_changelog_conflict_statement(
                issue_id, history_jid, jdoc),
            returning_id=self._get_returning_id())

        result = self.execute(sql, return_id=True)
        return result[0]
    
    def upsert_changelog_item(self, changelog_id, item):
        sql = "{insert_statment}\n{values_statement}\n{conflict_statement};".format(
            insert_statment=self._get_changelog_item_insert_statment(),
            values_statement=self._get_changelog_item_instance_values_statement(
                changelog_id, **item),
            conflict_statement=self._get_changelog_item_conflict_statement(**item))

        self.execute(sql)

    def refresh_materialized_view(self, name):
        sql = "REFRESH MATERIALIZED VIEW {name}".format(name=name)

        self.execute(sql)
