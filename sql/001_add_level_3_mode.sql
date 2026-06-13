SELECT COUNT(*) AS dolu_kayit
FROM users
WHERE NULLIF(TRIM(COALESCE(ucuncu_yonetici_sicil, '')), '') IS NOT NULL;