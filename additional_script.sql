CREATE TABLE IF NOT EXISTS sql_tasks (
    id SERIAL PRIMARY KEY,
    task_code VARCHAR(30) UNIQUE NOT NULL,
    project_id INT NOT NULL,
    title VARCHAR(200) NOT NULL,
    status VARCHAR(30) NOT NULL,
    assignee_id INT NOT NULL
);

CREATE TABLE IF NOT EXISTS sql_task_audit (
    id SERIAL PRIMARY KEY,
    task_id INT REFERENCES sql_tasks(id) ON DELETE CASCADE,
    actor_id INT NOT NULL,
    action VARCHAR(50) NOT NULL,
    details TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS sql_task_comments (
    id SERIAL PRIMARY KEY,
    task_id INT REFERENCES sql_tasks(id) ON DELETE CASCADE,
    author_id INT NOT NULL,
    body TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS sql_comment_attachments (
    id SERIAL PRIMARY KEY,
    comment_id INT REFERENCES sql_task_comments(id) ON DELETE CASCADE,
    file_name VARCHAR(255) NOT NULL,
    file_url TEXT NOT NULL,
    file_size_bytes BIGINT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_sql_task_audit_tid ON sql_task_audit(task_id);
CREATE INDEX IF NOT EXISTS idx_sql_task_comments_tid ON sql_task_comments(task_id);
CREATE INDEX IF NOT EXISTS idx_sql_comment_att_cid ON sql_comment_attachments(comment_id);
