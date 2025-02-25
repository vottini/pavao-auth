
WITH to_add AS (
	SELECT rl.id FROM pavao."role" rl WHERE
		rl.id = any($1::INTEGER[]) AND
		rl.code <> 'PAVAO::ADMIN_ROLE'
)

INSERT INTO pavao.assignment ("role", account)
	SELECT collected.id, $2 FROM to_add collected
	ON CONFLICT DO NOTHING;

