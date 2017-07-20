CREATE TABLE IF NOT EXISTS sprints (
    id          serial PRIMARY KEY,
    sprint_jid   integer NOT NULL UNIQUE,
    jdoc        jsonb NOT NULL,
    duration    tstzrange NOT NULL
);

CREATE INDEX ON sprints (sprint_jid);
CREATE INDEX ON sprints USING gist (duration);

COMMENT ON COLUMN sprints.sprint_jid IS 'JIRA Sprint Id';
COMMENT ON COLUMN sprints.jdoc IS 'JIRA sprint meta data';
COMMENT ON COLUMN sprints.duration IS 'tstzrage representing a sprints startDate and endDate';

CREATE TABLE IF NOT EXISTS sprint_issues (
    id                  serial PRIMARY KEY,
    sprint_id           integer REFERENCES sprints (id) NOT NULL,
    issue_jid           integer NOT NULL,
    issue_key           varchar(8) NOT NULL,
    jdoc                jsonb NOT NULL,
    added_during_sprint boolean,
    completed           boolean,
    punted              boolean,
    completed_in_another_sprint boolean,
    not_completed_in_current_sprint boolean,
    UNIQUE(sprint_id, issue_jid, issue_key)
);

CREATE INDEX ON sprint_issues (sprint_id, issue_jid, issue_key);

COMMENT ON COLUMN sprint_issues.issue_jid IS 'JIRA Issue Id';
COMMENT ON COLUMN sprint_issues.issue_key IS 'JIRA Issue Key (ex. PROJ-1234)';
COMMENT ON COLUMN sprint_issues.jdoc IS 'JIRA issue meta data';


CREATE TABLE IF NOT EXISTS issue_changelogs (
    id          serial PRIMARY KEY,
    issue_id    integer REFERENCES sprint_issues (id) NOT NULL,
    history_jid integer NOT NULL,
    jdoc        jsonb NOT NULL,
    UNIQUE(issue_id, history_jid)
);

COMMENT ON COLUMN issue_changelogs.history_jid IS 'JIRA ChangeLog History Id';
COMMENT ON COLUMN issue_changelogs.jdoc IS 'JIRA changelog meta data';

CREATE TABLE IF NOT EXISTS changelog_items (
    id              serial PRIMARY KEY,
    changelog_id    integer REFERENCES issue_changelogs (id) NOT NULL,
    field           varchar(255),
    field_type      varchar(255),
    field_id        varchar(255),
    from_id         varchar(255),
    from_string     text,
    to_id           varchar(255),
    to_string       text,
    UNIQUE(changelog_id, to_id, from_id)
);


DROP MATERIALIZED VIEW IF EXISTS sprint_view;
CREATE MATERIALIZED VIEW sprint_view AS
SELECT
    s.id, 
    s.sprint_jid, 
    si.issue_jid,
    cl.history_jid,
    s.jdoc->'name' AS name, 
    s.jdoc->'all_issues_estimate_sum'->'value' AS all_issues_estimate_sum,
    s.jdoc->'punted_issues_estimate_sum'->'value' AS punted_issues_estimate_sum,
    s.jdoc->'completed_issues_estimate_sum'->'value' AS completed_issues_estimate_sum,
    s.jdoc->'punted_issues_initial_estimate_sum'->'value' AS punted_issues_initial_estimate_sum,
    s.jdoc->'completed_issues_initial_estimate_sum'->'value' AS completed_issues_initial_estimate_sum,
    s.jdoc->'issues_not_completed_initial_estimate_sum'->'value' AS issues_not_completed_initial_estimate_sum,
    s.jdoc->'issues_completed_in_another_sprint_estimate_sum'->'value' AS issues_completed_in_another_sprint_estimate_sum,
    s.jdoc->'issues_completed_in_another_sprint_initial_estimate_sum'->'value' AS issues_completed_in_another_sprint_initial_estimate_sum,
    s.duration,
    si.jdoc->'summary' AS summary,
    si.jdoc->'description' AS description,
    si.jdoc->'assignee' AS assignee,
    si.jdoc->'assigneeName' AS assignee_name,
    si.jdoc as si_jdoc,
    si.added_during_sprint,
    si.completed,
    si.punted,
    si.completed_in_another_sprint,
    si.not_completed_in_current_sprint,
    to_timestamp(cl.jdoc->>'created', 'YYYY-MM-DD"T"HH24:MI:SS.MS"Z"') AS created,
    cl.jdoc as cl_jdoc,
    i.field,
    i.field_type,
    i.field_id,
    i.from_string,
    i.to_string
FROM
    sprints s JOIN 
        sprint_issues si ON
    s.id = sprint_id JOIN
        issue_changelogs cl ON
    si.id = cl.issue_id JOIN
        changelog_items i ON
    cl.id = i.changelog_id
WHERE 
    to_timestamp(cl.jdoc->>'created', 'YYYY-MM-DD') <@ s.duration
ORDER BY created;

