
SELECT
	acc.id,
	acc.login,
	acc.first_name,
	acc.last_name,
	acc.active,
	acc.id = $1 as my_account

	FROM pavao.account acc
	WHERE NOT acc.bot;

