import sqlite3

con = sqlite3.connect("main.sdb")
cur = con.cursor()

cur.execute("""
    CREATE TABLE users(
        id INT PRIMARY KEY,
        username TEXT,
        password TEXT,
        friends TEXT,
        banned TEXT,
        rank INT,
        reason TEXT,
        character TEXT,
        sbtoken TEXT,
        twostep TEXT,
        email TEXT,
        verified TEXT,
        code INT
    )
""")

cur.execute("""
    CREATE TABLE ipbans(
        reason TEXT,
        ip TEXT PRIMARY KEY
    )
""")

cur.execute("""
    CREATE TABLE verifytokens(
        token TEXT,
        for TEXT
    )
""")

con.commit()