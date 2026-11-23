USE unicareer;

SELECT role, is_active, COUNT(*) AS total_users
FROM users
GROUP BY role, is_active
ORDER BY role, is_active DESC;

SELECT status, COUNT(*) AS total_jobs
FROM job_posts
GROUP BY status;

SELECT j.job_id, j.title, c.company_name, j.status, j.deadline
FROM job_posts j
INNER JOIN companies c ON c.company_id = j.company_id
WHERE j.status = 'HIDDEN'
ORDER BY j.created_at DESC;

SELECT a.status, COUNT(*) AS total_applications
FROM applications a
GROUP BY a.status;

SET @candidate_id = 0;
SELECT a.application_id, j.title, a.ai_match_score, a.ai_feedback, a.applied_at
FROM applications a
INNER JOIN job_posts j ON j.job_id = a.job_id
WHERE a.candidate_id = @candidate_id
ORDER BY a.applied_at DESC;
