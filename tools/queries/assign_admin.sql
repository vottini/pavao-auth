
INSERT INTO pavao.assignment (account, "role")
	SELECT $1, id FROM pavao."role"
		WHERE admin;

