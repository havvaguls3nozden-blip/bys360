
CREATE UNIQUE INDEX IF NOT EXISTS uq_assignment_unique
ON evaluation_assignments (period_id, employee_id, evaluator_id, manager_level);
