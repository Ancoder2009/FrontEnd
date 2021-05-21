from flask import(
    Flask,
    render_template,
    make_response,
    abort,
    redirect,
    url_for,
    request
)
from sqlite3 import connect as con
from hashlib import sha256
from emod import send_mail
from secrets import token_urlsafe as gen_token
import random
from datetime import datetime, timedelta

con = con("main.sdb", check_same_thread=False)
cur = con.cursor()

app = Flask(__name__, template_folder="templates")

def validate():
    if "sbtoken" in request.cookies:
        cur.execute(f"SELECT username FROM users WHERE sbtoken = '{request.cookies.get('sbtoken')}'")
        res = cur.fetchone()
        if res == None:
            return False
        else:
            return res[0]
    else:
        return False

def validate_admin():
    if "sbtoken" in request.cookies:
        cur.execute(f"SELECT username, rank FROM users WHERE sbtoken = '{request.cookies.get('sbtoken')}'")
        res = cur.fetchone()
        if res == None:
            return False
        else:
            if res[1] >= 5:
                return res[0], res[1]
            else:
                return False
    else:
        return False

def check2step(username):
    cur.execute(f"SELECT twostep, verified, email FROM users WHERE username = '{username}'")
    res = cur.fetchone()
    if res[0] == "True" and res[1] == "True":
        return res[2]
    else:
        return False

def checkban(token):
    cur.execute(f"SELECT banned, reason FROM users WHERE sbtoken = '{request.cookies.get('sbtoken')}'")
    res = cur.fetchone()
    if res[0] == "True":
        return res[1]
    else:
        return False


@app.before_request
def before_request():
    ip = request.environ.get('REMOTE_ADDR')
    cur.execute(f"SELECT ip FROM ipbans WHERE ip = '{ip}'")
    res = cur.fetchone()
    if res != None:
        abort(403)
    else:
        if "sbtoken" in request.cookies:
            val = checkban(request.cookies.get("sbtoken"))
            if val == True:
                return render_template("banned.html", reason=res)
        else:
            pass

@app.route("/", methods=["POST", "GET"])
def index():
    return redirect(url_for("home"))

@app.route("/home", methods=["POST", "GET"])
def home():
    val = validate()
    if val == False:
        return redirect(url_for("login"))
    else:
        chk = checkban(request.cookies.get("sbtoken"))
        if chk == False:
            return render_template("home.html", username=val)
        else:
            return render_template("banned.html", reason=chk)

@app.route("/login", methods=["POST", "GET"])
def login():
    if request.method == "POST":
        if "method" in request.form and request.form.get("method") == "2step":
            username = request.form.get("username")
            password = request.form.get("password")
            code = request.form.get("code")
            res = check2step(username)
            if res == False:
                return redirect(url_for("home"))
            else:
                cur.execute(f"SELECT sbtoken FROM users WHERE username='{username}' AND password='{password}' AND code='{code}'")
                res = cur.fetchone()
                if res == None:
                    return render_template("twostep.html", message="Incorrect code!", username=username, password=password)
                else:
                    response = make_response(redirect(url_for("home")))
                    response.set_cookie("sbtoken", res[0])
                    return response
        else:
            username = request.form.get("username")
            pswdraw = request.form.get("password")
            password = sha256(pswdraw.encode()).hexdigest()
            cur.execute(f"SELECT sbtoken FROM users WHERE username='{username}' AND password='{password}'")

            res = cur.fetchone()
            if res == None:
                return render_template("login.html", message="Username or Password is invalid.")
            else:
                res = check2step(username)
                if res != False:
                    code = random.randint(1000, 9999)
                    cur.execute(f"UPDATE users SET code = '{code}' WHERE username='{username}' ")
                    send_mail(res, "no-reply", f"This is your Scratchblox verification code: {code}.")
                    con.commit()
                    return render_template("twostep.html", username=username, password=password)
                else:
                    cur.execute(f"SELECT sbtoken FROM users WHERE username='{username}' AND password='{password}'")

                    res = cur.fetchone()
                    response = make_response(redirect(url_for("home")))
                    response.set_cookie("sbtoken", res[0])
                    return response
    else:
        val = validate()
        if val == False:
            return render_template("login.html")
        else:
            return redirect(url_for("home"))

@app.route("/register", methods=["POST", "GET"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        pswdraw = request.form.get("password")
        password = sha256(pswdraw.encode()).hexdigest()
        cur.execute(f"SELECT username FROM users WHERE username = '{username}'")
        res = cur.fetchone()
        if res == None:
            if len(username) > 3:
                if len(username) < 12:
                    newtoken = gen_token(24)
                    cur.execute("SELECT COUNT(*) FROM users")
                    newid = cur.fetchone()[0] + 1
                    cur.execute("INSERT INTO users (id, username, password, friends, banned, rank, reason, character, sbtoken, twostep, email, verified, code, ip) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", (newid, username, password, "[]", "False", 1, None, None, newtoken, "False", None, "False", 0000, request.environ.get('REMOTE_ADDR')))
                    con.commit()
                    response = make_response(redirect(url_for("home")))
                    response.set_cookie("sbtoken", newtoken)
                    return response
                else:
                    return render_template("register.html", message="Username must be less than 11 chars!")
            else:
                 return render_template("register.html", message="Username must be more than 3 chars!")
        else:
            return render_template("register.html", message="Username is taken!")
    else:
        val = validate()
        if val == False:
            return render_template("register.html")
        else:
            return redirect(url_for("home"))

@app.route('/verify/<token>')
def verify(token):
    cur.execute(f"SELECT for FROM verifytokens WHERE token='{token}'")
    res = cur.fetchone()
    if res == None:
        return abort(404)
    else:
        cur.execute(f"UPDATE users SET verified = 'True' WHERE username = '{res[0]}'")
        cur.execute(f"DELETE FROM verifytokens WHERE token='{token}'") 
        con.commit()
        return "Successfully Verified!"
@app.route('/settings/<setting>', methods=["GET", "POST"])
def settings(setting):
    val = validate()
    username = val
    if val == False:
        return redirect(url_for("login"))
    else:
        settings = ['twostep']
        if setting in settings:
            if setting == "twostep":
                if request.method == "POST":
                    email = request.form.get("email")
                    passraw = request.form.get("password")
                    password = sha256(passraw.encode()).hexdigest()
                    cur.execute(f"SELECT id FROM users WHERE username = '{username}' AND password='{password}'")
                    res = cur.fetchone()
                    if res == None:
                        return render_template("twostepset.html", status="Incorrect password please try again.", style="color: red;")
                    else:
                        cur.execute(f"UPDATE users SET email = '{email}' WHERE username = '{username}' AND password='{password}'")
                        cur.execute(f"UPDATE users SET verified = 'False' WHERE username = '{username}' AND password='{password}'")
                        cur.execute(f"UPDATE users SET twostep = 'True' WHERE username = '{username}' AND password='{password}'")
                        token = gen_token(24)
                        con.commit()
                        cur.execute("INSERT INTO verifytokens (token, for) VALUES (?, ?)", (token, username))
                        send_mail(email, "no-reply", "Click this link to verify: https://scratchblox.tk/verify/" + token)
                        con.commit()

                        return render_template("twostepset.html", status=f"Verify this email: {email}", style="color: green;")
                else:
                    cur.execute(f"SELECT verified, email, twostep FROM users WHERE username = '{username}'")
                    res = cur.fetchone()
                    print(str(res) + "yes")
                    if res[2] == "False":
                        return render_template("twostepset.html", status="2 step verification is turned off.")
                    elif res[2] == "True" and res[0] == "False":
                        return render_template("twostepset.html", status=f"2 step verification is turned on but your email is not verified, email: {res[1]}.")
                    elif res[2] == "True" and res[0] == "True":
                        return render_template("twostepset.html", status=f"2 step verification is turned on. Email: {res[1]}.")
                    
        else:
            abort(404)

@app.route("/sitemap.xml")
def sitemap():
    rules = []
    for rule in app.url_map.iter_rules():
        numbers = []
        for letter in rules:
            i = 0
            if letter == "<":
                while True:
                    numbers.append(i)
                    if rule[i] == ">":
                        break
                    i += 1
                i += 1
        editingrule = list(rule)
        x = 0
        for number in numbers:
            editingrule[number] = ""
            if len(editingrule) == number + 1:
                editingrule[number] = "*"
            x += 1
        editedrule = "".join(editingrule)
        rules.append("https://scratchblox.tk" + editedrule)
    return rules

@app.route('/logout')
def logout():
    if "referer" in request.headers:
        try:
            request.headers.get("referer").index("scratchblox.tk")
            response = make_response(redirect(url_for("login")))
            response.set_cookie("sbtoken", "", max_age=0)
            return response
        except:
            return abort(404)
    else:
        return abort(404)

@app.route('/users/ban', methods=["POST", "GET"])    
def user_ban():
    if request.method == 'POST':
        val = validate_admin()
        if val == False:
            return abort(404)
        else:
            usertoban = request.form.get("username")
            reason = request.form.get("reason")

            if reason == "" or None:
                return render_template("banner.html", username=val[0], color="red", message="Username reason cannot be left blank.")
            else:
                cur.execute(f"SELECT banned, rank FROM users WHERE username='{usertoban}'")
                res = cur.fetchone()
                if res == None:
                    return render_template("banner.html", username=val[0], color="red", message=f"User {usertoban} does not exsist.")
                else:
                    if res[1] >= val[1]:
                        return render_template("banner.html", username=val[0], color="red", message="Cannot ban or unban user with more or equal power than you.")
                    else:
                        if res[0] == "True":
                            cur.execute(f"UPDATE users SET banned='False' WHERE username='{usertoban}'")
                            con.commit()
                            return render_template("banner.html", username=val[0], color="green", message=f"Unbanned {usertoban}.")
                        else:
                            cur.execute(f"UPDATE users SET banned='True' WHERE username='{usertoban}'")
                            cur.execute(f"UPDATE users SET reason='{reason}' WHERE username='{usertoban}'")
                            con.commit()
                            return render_template("banner.html", username=val[0], color="yellow", message=f"Banned {usertoban}.")
    else:
        val = validate_admin()
        if val == False:
            return abort(404)
        else:
            return render_template("banner.html", username=val[0])

@app.route('/users/ipban', methods=["POST", "GET"])    
def user_ipban():
    if request.method == 'POST':
        val = validate_admin()
        if val == False:
            return abort(404)
        else:
            usertoban = request.form.get("username")
            reason = request.form.get("reason")

            if reason == "" or None:
                return render_template("banner.html", username=val[0], color="red", message="Username reason cannot be left blank.")
            else:
                cur.execute(f"SELECT ip, rank FROM users WHERE username='{usertoban}'")
                ip_rank = cur.fetchone()
                if ip_rank == None:
                    return render_template("banner.html", username=val[0], color="red", message=f"User {usertoban} does not exsist.")
                else:
                    if ip_rank >= val[1]:
                        return render_template("banner.html", username=val[0], color="red", message="Cannot ip ban or unban user with more or equal power than you.")
                    else:
                        cur.execute("SELECT ip FROM ipbans WHERE ip='{ip}'")
                        res = cur.fetchone()
                        if not res == None:
                            cur.execute(f"DELETE FROM ipbans WHERE ip='{ip_rank[0]}'")
                            con.commit()
                            return render_template("banner.html", username=val[0], color="green", message=f"Unipbanned {usertoban}.")
                        else:
                            cur.execute(f"INSERT INTO ipbans (ip, reason) VALUES (?, ?)", (ip_rank[0], reason))
                            con.commit()
                            return render_template("banner.html", username=val[0], color="yellow", message=f"Banned {usertoban}.")
    else:
        val = validate_admin()
        if val == False:
            return abort(404)
        else:
            return render_template("banner.html", username=val[0])

@app.route('/users/<id>')
def users(id):
    cur.execute(f"SELECT username, rank FROM users WHERE id='{id}'")
    res = cur.fetchone()
    if res == None:
        return abort(404)
    else:
        if res[1] >= 5:
            if id == 1:
                return render_template("user.html", username=res[0] + "☑️")
            else:
                return render_template("user.html", username=res[0] + "☑️", img="https://u.cubeupload.com/Oooof/Webcapture2142021155.jpeg")
        else:
            return render_template("user.html", username=res[0])

if __name__ == "__main__": 
    app.run("0.0.0.0", debug=False)