import MySQLdb
from flask import Flask, jsonify, redirect, render_template, request, url_for, session
from flask_jsglue import JSGlue
from flask_session import Session
from passlib.apps import custom_app_context as pwd_context
from tempfile import mkdtemp
from flask_bcrypt import Bcrypt
from flaskext.mysql import MySQL

from helpers import apology, email_spyro, getSong, get_text, login_required, redirect_dest
from classes import Songs

# configure application
app = Flask(__name__)
JSGlue(app)
bcrypt = Bcrypt(app)
mysql = MySQL()

# ensure responses aren't cached
if app.config["DEBUG"]:
    @app.after_request
    def after_request(response):
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Expires"] = 0
        response.headers["Pragma"] = "no-cache"
        return response

# configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)
app.config["JSONIFY_PRETTY _REGULAR"] = False

config = {
    'user': 'TheGreek9',
    'password': 'oatmealcookie',
    'host': 'TheGreek9.mysql.pythonanywhere-services.com',
    'database' : 'TheGreek9$musicalsite'
}

conn = MySQLdb.connect(**config)
db = conn.cursor(MySQLdb.cursors.DictCursor)

@app.route("/", methods=["GET", "POST"])
def index():

    if request.method == "POST":
        if get_text("musical") == "All Musicals":
            if get_text("musicalSongs") and not get_text("nonMusicalSongs"):

                songList = Songs("N/A","musical").query_table()

            elif not get_text("musicalSongs") and get_text("nonMusicalSongs"):

                songList = Songs("N/A","non musical").query_table()

            else:

                songList = Songs("N/A").query_table()

            return render_template("allresults.html", songList=songList)

        else:
            music = '%' + get_text("musical") + '%'

            db.execute("SELECT * FROM musicals WHERE musical LIKE %s", [music])
            musicalList = db.fetchall()
            role = get_text("role")

            if len(musicalList) != 1:
                return render_template("searcherror.html")

            if role == "All Roles":
                if get_text("musicalSongs") and not get_text("nonMusicalSongs"):

                    songList = Songs("N/A", "musical", musicalList[0]["Id"]).query_table()

                elif not get_text("musicalSongs") and get_text("nonMusicalSongs"):

                    songList = Songs("N/A", "non musical", musicalList[0]["Id"]).query_table()

                else:

                    songList = Songs("N/A", None, musicalList[0]["Id"]).query_table()

                return render_template("results.html", musicalList=musicalList, songList=songList)

            else:
                if get_text("musicalSongs") and not get_text("nonMusicalSongs"):

                    songList = Songs("N/A", "musical", musicalList[0]["Id"], role).query_table()

                elif not get_text("musicalSongs") and get_text("nonMusicalSongs"):

                    songList = Songs("N/A","non musical", musicalList[0]["Id"], role).query_table()

                else:

                    songList = Songs("N/A", None, musicalList[0]["Id"], role).query_table()

                return render_template("results.html", musicalList=musicalList, songList=songList, pickedRole=role)

    else:
        return render_template("search.html")

@app.route("/changepassword", methods=["GET", "POST"])
@login_required
def changepassword():

    if request.method == "POST":

        db.execute("SELECT * FROM users WHERE userId = %s", [Session["user_id"]])

        rows = db.fetchall()

        if not pwd_context.verify(get_text("old password"), rows[0]["password"]):
            return apology("Invalid password")

        db.execute("UPDATE users SET password=%s WHERE userId=%s", [session["user_id"], pwd_context.hash(get_text("new password"))])
        conn.commit()

        return redirect(url_for("index"))

    else:
        return render_template("changepassword.html")

@app.route("/getspotifyinfo", methods=["GET", "POST"])
def getspotifyinfo():

    track = request.args.get("track")
    artist = request.args.get("artist")

    spotifyDict = getSong(track, artist)

    if request.method == "POST":

        originalSongId = request.args.get("id")
        chosenSongId = int(get_text("songCheck"))
        chosenSongId -= 1
        chosenSpotifyId = spotifyDict[chosenSongId]['id']
        chosenSpotifyPrev = spotifyDict[chosenSongId]['preview']

        db.execute("UPDATE songs SET spotifyId=%s, spotifyPrev=%s WHERE songId=%s", [chosenSpotifyId, chosenSpotifyPrev, originalSongId])
        conn.commit()

        return redirect(url_for('review'))

    else:

        return render_template("reviewspotify.html", spotifyDict=spotifyDict)

@app.route("/login", methods=["GET", "POST"])
def login():
# forget any user_id
    session.clear()

    # if user reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # query database for username
        db.execute("SELECT * FROM users WHERE userEmail = %s", [get_text("username")])
        rows = db.fetchall()

        # ensure username exists and password is correct
        if len(rows) != 1 or not pwd_context.verify(get_text("password"), rows[0]["password"]):
            return apology("invalid username and/or password")

        # remember which user has logged in
        session["user_id"] = rows[0]["userId"]
        session["first_name"] = rows[0]["firstName"]

        # redirect user to home page
        return redirect_dest("index")

    # else if user reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")

@app.route("/logout")
def logout():

    # forget any user_id
    session.clear()

    return redirect(url_for("index"))

@app.route("/newsong", methods=["GET", "POST"])
@login_required
def newSong():
    if request.method == "POST":

        if get_text("songName"):

            db.execute("SELECT Id FROM musicals WHERE musical=%s", [get_text("newMusical")])
            idData = db.fetchall()

            Songs('pending').create_song(request.form, idData[0]['Id'])

            email_spyro()

            return render_template('submissionsong.html')

        else:
            return apology("Something went wrong")
    else:
        return render_template("newsong.html")

@app.route("/newmusical", methods=["GET", "POST"])
@login_required
def newmusical():
    if request.method == "POST":

        if get_text("musicalName"):

            db.execute("INSERT INTO musicals (musical, playwright, composer, lyricist, genre, production_year, plot, pendingNon) \
            VALUES (%s, %s, %s, %s, %s, %s, %s, 'pending')", [get_text("musicalName"), get_text("playwright"), get_text("musicalComposer"),
            get_text("lyricist"), get_text("musicalGenre"), get_text("productionYear"), get_text("plot")])
            conn.commit()

            email_spyro()

            return render_template("submissionmusical.html")

        else:
            return apology("Something went wrong")
    else:

        return render_template("newmusical.html")

@app.route("/register", methods=["GET", "POST"])
def register():

    session.clear()

    if request.method == "POST":

        # query database for username

        db.execute("SELECT * FROM users WHERE userEmail = %s", [get_text("username")])

        rows = db.fetchall()

        # ensure username does not exists and password is correct
        if len(rows) != 0:
            return apology("invalid username")


        db.execute("INSERT INTO users (userEmail, password, firstName, lastName) VALUES (%s, %s, %s, %s)",
        [get_text("username"), pwd_context.hash(get_text("password")), get_text("first name"), get_text("last name")])
        conn.commit()

        session["user_id"] = get_text("username")
        session["first_name"] = get_text("first name")

        return redirect_dest("index")

    else:
        return render_template("register.html")

@app.route("/review", methods=["GET", "POST"])
@login_required
def review():
    if request.method == "POST":
        if session["user_id"] == 1:
            if 'addSong' in request.form or 'deleteSong' in request.form:
                checking = request.form.getlist("checkingSong")

                if 'addSong' in request.form:
                    for checked in checking:
                        Songs('N/A', None, None, None, int(checked)).add_song_to_db()

                elif 'deleteSong' in request.form:
                    for checked in checking:
                        Songs('pending', None, None, None, int(checked)).remove_song()

            elif 'addMusical' in request.form or 'deleteMusical' in request.form:
                checking = request.form.getlist("checkingMusical")

                if 'addMusical' in request.form:
                    for checked in checking:

                        db.execute("UPDATE musicals SET pendingNon='N/A' WHERE Id=%s", [int(checked)])
                        conn.commit()

                elif 'deleteMusical' in request.form:
                    for checked in checking:

                        db.execute("DELETE FROM musicals WHERE (Id=%s AND pendingNon='pending')", [int(checked)])
                        conn.commit()

            else:
                return apology("Somtething's wrong")

            try:

                songList = Songs("pending").query_table()

            except:

                db.execute("SELECT * FROM musicals WHERE pendingNon='pending'")

            musicalList = db.fetchall()

            return render_template("review.html", songList=songList)
        else:
            return apology("You are not authorized to view this")
    else:
        if session["user_id"] == 1:

            songList = Songs("pending").query_table()

            db.execute("SELECT * FROM musicals WHERE pendingNon='pending'")

            musicalList = db.fetchall()

            return render_template("review.html", songList=songList, musicalList=musicalList)
        else:
            return apology("You are not authorized to view this")

@app.route("/roles", methods=["GET"])
def roles():

    try:
        music = request.args.get("music")

        data = Songs("N/A").distinct_role(music)

        return jsonify(data)
    except:
        return jsonify([])

@app.route("/search", methods=["GET"])
def search():
    urlstring = "%" + request.args.get("que") + "%"

    if urlstring != "%%":

        query = "SELECT * FROM musicals WHERE (musical LIKE %(url)s AND pendingNon != %(pendingNon)s)"
        params = { 'url' : urlstring, 'pendingNon' : 'pending'}

        db.execute(query, params)

        #db.execute("SELECT * FROM musicals WHERE (musical LIKE %s AND pendingNon != 'pending')", [urlstring])
        data = db.fetchall()
    else:
        return jsonify([])

    try:
        return jsonify(data)
    except:
        return jsonify(username="somethings wrong")