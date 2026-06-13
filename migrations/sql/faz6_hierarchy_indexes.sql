-- BYS360 Hiyerarşi Stabilizasyonu için önerilen indexler
CREATE INDEX IF NOT EXISTS ix_users_sicil_no ON users (sicil_no);
CREATE INDEX IF NOT EXISTS ix_users_yonetici_sicil ON users (yonetici_sicil);
CREATE INDEX IF NOT EXISTS ix_users_ikinci_yonetici_sicil ON users (ikinci_yonetici_sicil);
CREATE INDEX IF NOT EXISTS ix_users_ucuncu_yonetici_sicil ON users (ucuncu_yonetici_sicil);
CREATE INDEX IF NOT EXISTS ix_eval_assignment_period_employee_level ON evaluation_assignments (period_id, employee_id, manager_level);
CREATE INDEX IF NOT EXISTS ix_perf_eval_period_employee ON performance_evaluations (period_id, employee_id);
