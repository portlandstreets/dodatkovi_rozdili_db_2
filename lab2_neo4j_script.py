from neo4j import GraphDatabase

URI = "bolt://localhost:7687"
AUTH = ("neo4j", "123456789")

driver = GraphDatabase.driver(URI, auth=AUTH)

with driver.session() as session:
    session.run("MATCH (n) DETACH DELETE n")

    session.run("""
        CREATE (p:Project {code: 'ERP-2026', name: 'Corporate ERP Migration', budget: 150000})
        CREATE (m:Employee {id: 1, name: 'Oleksandr Tkalia', role: 'Project Manager'})
        CREATE (d1:Employee {id: 2, name: 'Ivan Kovalenko', role: 'DevOps Engineer'})
        CREATE (d2:Employee {id: 3, name: 'Maria Boyko', role: 'Backend Developer'})
        
        CREATE (t1:Task {code: 'TASK-101', title: 'Setup Docker & CI/CD', status: 'DONE', hours: 16})
        CREATE (t2:Task {code: 'TASK-102', title: 'Design Auth Microservice', status: 'IN_PROGRESS', hours: 24})
        CREATE (t3:Task {code: 'TASK-103', title: 'Deploy to Production Cluster', status: 'TODO', hours: 8})

        CREATE (m)-[:MANAGES]->(p)
        CREATE (d1)-[:WORKS_ON]->(p)
        CREATE (d2)-[:WORKS_ON]->(p)

        CREATE (t1)-[:PART_OF]->(p)
        CREATE (t2)-[:PART_OF]->(p)
        CREATE (t3)-[:PART_OF]->(p)

        CREATE (d1)-[:ASSIGNED_TO]->(t1)
        CREATE (d2)-[:ASSIGNED_TO]->(t2)
        CREATE (d1)-[:ASSIGNED_TO]->(t3)

        CREATE (t1)-[:BLOCKS]->(t2)
        CREATE (t2)-[:BLOCKS]->(t3)
    """)
    print("1. Graph nodes and relationships created successfully.\n")

    print("2. Critical dependency chain (Task blocking path):")
    res_chain = session.run("""
        MATCH (t1:Task)-[:BLOCKS]->(t2:Task)-[:BLOCKS]->(t3:Task)
        RETURN t1.code AS first_task, t2.code AS second_task, t3.code AS final_task
    """)
    for r in res_chain:
        print(f"   {r['first_task']} -> BLOCKS -> {r['second_task']} -> BLOCKS -> {r['final_task']}")

    print("\n3. Employees and their assigned tasks in project ERP-2026:")
    res_team = session.run("""
        MATCH (e:Employee)-[:ASSIGNED_TO]->(t:Task)-[:PART_OF]->(p:Project {code: 'ERP-2026'})
        RETURN e.name AS employee, e.role AS role, t.code AS task_code, t.title AS title, t.status AS status
    """)
    for r in res_team:
        print(f"   {r['employee']} ({r['role']}) -> [{r['task_code']}] {r['title']} ({r['status']})")

    session.run("""
        MATCH (t:Task {code: 'TASK-102'})
        SET t.status = 'DONE'
    """)
    print("\n4. Updated TASK-102 status to 'DONE'.")

    session.run("""
        MATCH (:Task {code: 'TASK-102'})-[rel:BLOCKS]->(:Task {code: 'TASK-103'})
        DELETE rel
    """)
    print("5. Removed BLOCKS relationship between TASK-102 and TASK-103.")

    res_unblocked = session.run("""
        MATCH (t:Task {code: 'TASK-103'})
        WHERE NOT (:Task)-[:BLOCKS]->(t)
        RETURN t.code AS code, t.title AS title
    """)
    for r in res_unblocked:
        print(f"6. Verified unblocked task ready for work: [{r['code']}] {r['title']}")

driver.close()