
UPDATE task
	SET enabled = :enabled
	WHERE id = :task_id;

