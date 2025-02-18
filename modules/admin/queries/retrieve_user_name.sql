
SELECT
	id,
	login,
	first_name,
	last_name,
	active

	FROM pavao.account
	WHERE id = $1;

