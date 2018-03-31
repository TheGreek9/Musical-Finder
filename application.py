import MySQLdb
import logging
import logging.config
from flask import Flask, jsonify, redirect, render_template, request, url_for, session
from flask_jsglue import JSGlue
from flask_session import Session
from tempfile import mkdtemp
from flask_bcrypt import Bcrypt
from flaskext.mysql import MySQL
from helpers import *
from classes import *
from databaseconfig import errorLoggerFile

# configure application
app = Flask(__name__)
JSGlue(app)
mysql = MySQL()
baseLogger = logging.getLogger()

#configure error loggers
gm = GMailHandler()
gm.setLevel(logging.DEBUG)
gmFormatter = logging.Formatter('%(name)s called: Problem with %(funcName)s function in %(filename)s')
gm.setFormatter(gmFormatter)

fh = logging.FileHandler(errorLoggerFile)
fh.setLevel(logging.DEBUG)
fhFormatter = logging.Formatter("File: '%(pathname)s'\n%(asctime)s Failed: Line %(lineno)d in %(filename)s\n\
Error: %(message)s\n")
fh.setFormatter(fhFormatter)

baseLogger.addHandler(gm)
baseLogger.addHandler(fh)

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

@app.route("/", methods=["GET", "POST"])
def index():

    if request.method == "POST":
        if request.form.get("musical") == "All Musicals":
            if request.form.get("musicalSongs") and not request.form.get("nonMusicalSongs"):

                songList = Songs("N/A","musical").query_table()

            elif not request.form.get("musicalSongs") and request.form.get("nonMusicalSongs"):

                songList = Songs("N/A","non musical").query_table()

            else:

                songList = Songs("N/A").query_table()

            return render_template("allresults.html", songList=songList)

        else:
            music = '%' + request.form.get("musical") + '%'
            musicalList = Musicals("N/A", music).query_table()

            role = request.form.get("role")

            if len(musicalList) != 1:
                return apology("We apologize but we currently do not have that musical in our database.",
                "Would you like to add it?", "Not Found", request.endpoint, "Add Musical")

            if role == "All Roles":
                if request.form.get("musicalSongs") and not request.form.get("nonMusicalSongs"):

                    songList = Songs("N/A", "musical", musicalList[0]["Id"]).query_table()

                elif not request.form.get("musicalSongs") and request.form.get("nonMusicalSongs"):

                    songList = Songs("N/A", "non musical", musicalList[0]["Id"]).query_table()

                else:

                    songList = Songs("N/A", None, musicalList[0]["Id"]).query_table()


            else:
                if request.form.get("musicalSongs") and not request.form.get("nonMusicalSongs"):

                    songList = Songs("N/A", "musical", musicalList[0]["Id"], role).query_table()

                elif not request.form.get("musicalSongs") and request.form.get("nonMusicalSongs"):

                    songList = Songs("N/A","non musical", musicalList[0]["Id"], role).query_table()

                else:

                    songList = Songs("N/A", None, musicalList[0]["Id"], role).query_table()

            if songList == -1 or musicalList == -1:
                return apology("There was an error with our database", "Error", "We're Sorry", None)
            else:
                return render_template("results.html", musicalList=musicalList, songList=songList, pickedRole=role)

    else:
        try:
            test_connection()
        except Exception:
            return apology("There was a problem connecting to our database", "Error", "We're Sorry", None)

        try:
            return render_template("search.html")
        except:
            baseLogger.exception("Unable to render search.html")
            return apology("There was a problem connecting to our site", "Error", "We're Sorry", None)

@app.route("/allmusicals", methods=["GET"])
def allmusicals():
    musicalList = Musicals().query_table()

    return render_template("allresults.html", musicalList=musicalList)

@app.route("/changepassword", methods=["GET", "POST"])
@login_required
def changepassword():

    if request.method == "POST":

        if not session["user_id"]:
            baseLogger.error('No session user ID when changing password')
            return apology("There was an error with user information", "Please log in and try again",
            "We're Sorry")

        userinfo = Users(session["user_id"]).query_table()

        result = check_password(userinfo['password'], request.form.get("old password"))

        if result == False:
            return render_template("changepassword.html", passError=True)

        newPassword = hash_password(request.form.get("new password"))

        Users(session["user_id"]).change_password(newPassword)

        return redirect(url_for("index"))

    else:
        return render_template("changepassword.html")

@app.route("/getspotifyinfo", methods=["GET", "POST"])
def getspotifyinfo():

    if request.method == "POST":

        originalSongId = request.args.get("id")
        chosenSongId = int(request.form.get("songCheck"))
        chosenSongId -= 1
        chosenSpotifyId = spotifyDict[chosenSongId]['id']
        chosenSpotifyPrev = spotifyDict[chosenSongId]['preview']

        Songs(None, None, None, None, originalSongId).add_spotify_info(chosenSpotifyId, chosenSpotifyPrev)

        return redirect(url_for('review'))

    else:
        track = request.args.get("track")
        artist = request.args.get("artist")

        spotifyDict = getSong(track, artist)

        if spotifyDict == -1:
            return apology("Not able to get spotifyDict in /getspotify route", "Check the error logs")
        else:
            return render_template("reviewspotify.html", spotifyDict=spotifyDict)

@app.route("/login", methods=["GET", "POST"])
def login():
# forget any user_id
    session.clear()

    # if user reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # query database for username
        userinfo = Users(None, request.form.get("userEmail")).query_table()

        if userinfo == None:
            return render_template("login.html", loginError=True)
        elif userinfo == -1:
            return apology("Error while attempting to login")

        result = check_password(userinfo['password'], request.form.get("password"))

        if result == False:
            return render_template("login.html", loginError=True)

        # remember which user has logged in
        session["user_id"] = userinfo["userId"]
        session["first_name"] = userinfo["firstName"]

        # redirect user to home page
        return redirect_dest("index")

    # else if user reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html", error=False)

@app.route("/logout")
def logout():

    # forget any user_id
    session.clear()

    return redirect(url_for("index"))

@app.route("/newsong", methods=["GET", "POST"])
def newsong():
    if request.method == "POST":

        idData = Musicals().get_Id(request.form.get("newMusical"))

        if idData == -1:
            return apology("We were unable to find that musical")

        #Songs('pending').create_song(request.form, idData['Id'], session["user_id"])

        Songs('pending').create_song(request.form, idData['Id'], 1)

        email_spyro("There's a new song addition to the database", "http://thegreek9.pythonanywhere.com/login?next=review")

        return render_template("submissionconfirm.html", newitem="http://127.0.0.1:5000/#newsongSection")

    else:
        return render_template("newsong.html")

@app.route("/newmusical", methods=["GET", "POST"])
def newmusical():
    if request.method == "POST":

        #Musicals('pending').create_musical(request.form, session["user_id"])

        Musicals('pending').create_musical(request.form, 1)

        email_spyro("There's a new musical addition to the database", "http://thegreek9.pythonanywhere.com/login?next=review")

        return render_template("submissionconfirm.html", newitem="http://127.0.0.1:5000/#newmusicalSection")

    else:

        return render_template("newmusical.html")

@app.route("/register", methods=["GET", "POST"])
def register():

    session.clear()

    if request.method == "POST":

        # query database for username

        userinfo = Users(None, request.form.get("userEmail")).query_table()

        if userinfo != None:
            return render_template("register.html", registerError=True)
        elif userinfo == -1:
            return apology("There was an error trying to register")

        Users().add_user_to_db(request.form)

        userinfo = Users(None, request.form.get("userEmail")).query_table()

        if userinfo == None:
             baseLogger.error("User info was not found after user registered. Unable to add info to session.")
        elif userinfo == -1:
            baseLogger.error("Class returned error when trying to access user info. Not able to add info to session.")
        else:
            session["user_id"] = userinfo['userId']
            session["first_name"] = userinfo['firstName']

        return redirect_dest("index")

    else:
        return render_template("register.html", registerError=False)

@app.route("/review", methods=["GET", "POST"])
@login_required
def review():
    if request.method == "POST":
        if session["user_id"] == 1:
            if 'addSong' in request.form or 'deleteSong' in request.form:
                checked = request.form.getlist("checkedSong")

                if 'addSong' in request.form:
                    for songNum in checked:
                        Songs('N/A', None, None, None, int(songNum)).add_song_to_db()

                elif 'deleteSong' in request.form:
                    for songNum in checked:
                        Songs('pending', None, None, None, int(songNum)).remove_song()

            elif 'addMusical' in request.form or 'deleteMusical' in request.form:
                checked = request.form.getlist("checkedMusical")

                if 'addMusical' in request.form:
                    for musicalNum in checked:

                        Musicals('N/A', None, int(musicalNum)).add_musical_to_db()

                elif 'deleteMusical' in request.form:
                    for musicalNum in checked:

                        Musicals('pending', None, int(musicalNum)).remove_musical()

            else:
                assert("Add Song or Delete Song was not in POST request sent to review. But POST was sent anyway")

            songList = Songs("pending").query_table()

            if songList == -1:
                return apology("There was an error when calling query table from Song class", "Check error logs", "Error", None)

            musicalList = Musicals("pending").query_table()

            if musicalList == -1:
                return apology("There was an error when calling query table from Song class", "Check error logs", "Error", None)

            return render_template("review.html", songList=songList, musicalList=musicalList)

        else:
            return redirect(url_for("index"))
    else:
        if session["user_id"] == 1:

            songList = Songs("pending").query_table()

            if songList == -1:
                return apology("There was an error when calling query table from Song class", "Check error logs", "Error", None)

            musicalList = Musicals("pending").query_table()

            if musicalList == -1:
                return apology("There was an error when calling query table from Song class", "Check error logs", "Error", None)

            return render_template("review.html", songList=songList, musicalList=musicalList)
        else:
            return redirect(url_for("index"))

@app.route("/roles", methods=["GET"])
def roles():

    musicalId = Musicals().get_Id(request.args.get("music"))

    if musicalId == None:
        return jsonify([])
    elif musicalId == -1:
        return jsonify([])

    data = Songs("N/A").distinct_role(musicalId)

    if data == None:
        return jsonify([])
    elif data == -1:
        return jsonify([])
    else:
        return jsonify(data)

@app.route("/search", methods=["GET"])
def search():
    urlstring = "%" + request.args.get("que") + "%"

    if urlstring != "%%":

        data = Musicals("N/A", urlstring).query_table()

        if data == None:
            return jsonify([])
        elif data == -1:
            return jsonify([])
        else:
            return jsonify(data)
    else:
        return jsonify([])
