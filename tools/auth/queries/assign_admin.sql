
INSERT INTO pavao.assignment (account, "role")
	SELECT $1, id FROM pavao."role"
		WHERE code = 'PAVAO::ADMIN_ROLE';

