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
    si.added_during_sprint,
    si.completed,
    si.punted,
    si.completed_in_another_sprint,
    si.not_completed_in_current_sprint,
    to_timestamp(cl.jdoc->>'created', 'YYYY-MM-DD"T"HH24:MI:SS.MS"Z"') AS created,
    cl.jdoc
FROM
    sprints s JOIN 
        sprint_issues si ON
    s.id = sprint_id JOIN
        issue_changelogs cl ON
    si.id = cl.issue_id
WHERE 
    to_timestamp(cl.jdoc->>'created', 'YYYY-MM-DD') <@ s.duration
ORDER BY created;

/* select all sprint issues and their changelogs within the sprint, order by change created date */
SELECT
    s.id, s.sprint_jid, 
    s.jdoc->'name' AS name, 
    s.duration,
    si.jdoc->'summary' AS summary,
    to_timestamp(cl.jdoc->>'created', 'YYYY-MM-DD"T"HH24:MI:SS.MS"Z"') AS created  
FROM
    sprints s JOIN 
        sprint_issues si ON
    s.id = sprint_id JOIN
        issue_changelogs cl ON
    si.id = cl.issue_id
WHERE 
    s.id = 3
    AND to_timestamp(cl.jdoc->>'created', 'YYYY-MM-DD') <@ s.duration
ORDER BY created;
