SELECT id, period_id, employee_id, evaluator_id, manager_level, status
FROM evaluation_assignments
WHERE manager_level = 3
ORDER BY id DESC;