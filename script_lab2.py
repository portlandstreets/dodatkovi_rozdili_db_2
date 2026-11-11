import random
import time
import psycopg2
from pymongo import MongoClient

PG_DSN = "dbname=corporate_managment user=postgres password=123 host=127.0.0.1 port=5432 client_encoding=utf8"
MONGO_URI = "mongodb://localhost:27017/"

print("Connecting to PostgreSQL and MongoDB...")
pg_conn = psycopg2.connect(PG_DSN)
pg_cur = pg_conn.cursor()

mongo_client = MongoClient(MONGO_URI)
mongo_db = mongo_client["corp_pm_nosql"]
mongo_col = mongo_db["task_cards"]

print("Clearing old data and generating 1,000 entities...")
pg_cur.execute("TRUNCATE sql_tasks CASCADE;")
pg_conn.commit()
mongo_col.delete_many({})

NUM_RECORDS = 1000

for i in range(1, NUM_RECORDS + 1):
    doc = {
        "_id": f"TASK-{i}",
        "project_id": 1,
        "title": f"Task number {i}",
        "status": "IN_PROGRESS",
        "assignee_id": 2,
        "audit": [{"action": "UPDATE", "step": j, "ts": time.time()} for j in range(5)],
        "comments": [{"author_id": 1, "body": f"Comment {j}", "attachment": "file.pdf"} for j in range(3)]
    }
    mongo_col.insert_one(doc)

    pg_cur.execute(
        "INSERT INTO sql_tasks (id, task_code, project_id, title, status, assignee_id) VALUES (%s, %s, %s, %s, %s, %s)",
        (i, f"TASK-{i}", 1, f"Task number {i}", "IN_PROGRESS", 2)
    )
    for j in range(5):
        pg_cur.execute(
            "INSERT INTO sql_task_audit (task_id, actor_id, action, details) VALUES (%s, %s, %s, %s)",
            (i, 1, "UPDATE", f"Step {j}")
        )
    for j in range(3):
        pg_cur.execute(
            "INSERT INTO sql_task_comments (task_id, author_id, body) VALUES (%s, %s, %s) RETURNING id",
            (i, 1, f"Comment {j}")
        )
        cid = pg_cur.fetchone()[0]
        pg_cur.execute(
            "INSERT INTO sql_comment_attachments (comment_id, file_name, file_url, file_size_bytes) VALUES (%s, %s, %s, %s)",
            (cid, "file.pdf", "http://s3.corp/file.pdf", 1024)
        )

pg_conn.commit()
print("Data generation completed. Running benchmark...")

sample_ids = [random.randint(1, NUM_RECORDS) for _ in range(1000)]

start_pg = time.perf_counter()
for tid in sample_ids:
    pg_cur.execute("""
        SELECT t.id, t.title, a.action, c.body, att.file_name
        FROM sql_tasks t
        LEFT JOIN sql_task_audit a ON t.id = a.task_id
        LEFT JOIN sql_task_comments c ON t.id = c.task_id
        LEFT JOIN sql_comment_attachments att ON c.id = att.comment_id
        WHERE t.id = %s;
    """, (tid,))
    _ = pg_cur.fetchall()
pg_read_time = time.perf_counter() - start_pg

start_mongo = time.perf_counter()
for tid in sample_ids:
    _ = mongo_col.find_one({"_id": f"TASK-{tid}"})
mongo_read_time = time.perf_counter() - start_mongo

print("\n" + "=" * 60)
print("PERFORMANCE BENCHMARK RESULTS (1,000 Reads)")
print("=" * 60)
print(f"PostgreSQL (4 JOINs):  {pg_read_time:.3f} s (avg: {(pg_read_time / 1000) * 1000:.2f} ms/query)")
print(f"MongoDB (1 document):  {mongo_read_time:.3f} s (avg: {(mongo_read_time / 1000) * 1000:.2f} ms/query)")
print(f"NoSQL Speedup:         {pg_read_time / mongo_read_time:.2f}x faster")
print("=" * 60)

pg_cur.close()
pg_conn.close()