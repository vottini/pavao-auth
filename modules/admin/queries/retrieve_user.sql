
SELECT
	login,
	first_name,
	last_name,
	active,
	creation,
	last_login

FROM pavao.account
WHERE id = $1;

