-- Mükerrer görev üretimini azaltmak için önerilen unique guard
CREATE UNIQUE INDEX IF NOT EXISTS uq_eval_assignment_period_employee_evaluator_level
    ON evaluation_assignments (period_id, employee_id, evaluator_id, manager_level);
