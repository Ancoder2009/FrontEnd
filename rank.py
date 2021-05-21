import sqlite3
con = sqlite3.connect("main.sdb")
cur = con.cursor()

username = input("Username:")
arg = input("Arg: ")
mode = input("U/R: ")
if mode.lower() == "u":
    cur.execute(f"UPDATE users SET username='{arg}' WHERE username='{username}'")
else:
    cur.execute(f"UPDATE users SET rank='{arg}' WHERE username='{username}'")

con.commit()
con.close()