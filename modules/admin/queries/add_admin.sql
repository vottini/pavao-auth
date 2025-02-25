
WITH found_user AS (
	SELECT id FROM pavao.account
		WHERE id = $1
)

INSERT INTO pavao.assignment (account, "role")
	SELECT found.id, rl.id
		FROM found_user found
		CROSS JOIN pavao."role" rl
		WHERE rl.code = 'PAVAO::ADMIN_ROLE'

	ON CONFLICT DO NOTHING;

