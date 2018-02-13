import MySQLdb
from flask import Flask, jsonify, redirect, render_template, request, url_for, session
from flask_jsglue import JSGlue
from flask_session import Session
from passlib.apps import custom_app_context as pwd_context
from tempfile import mkdtemp
from flask_bcrypt import Bcrypt
from flaskext.mysql import MySQL
from helpers import *
from classes import *

# configure application
app = Flask(__name__)
JSGlue(app)
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
            musicalList = Musicals("N/A", music).query_table()

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

        userinfo = Users(session["user_id"]).query_table()

        result = check_password(userinfo['password'], request.form.get("old password"))

        if result == False:
            return apology("Invalid Credentials")

        newPassword = hash_password(request.form.get("new password"))

        Users(session["user_id"]).change_password(newPassword)

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

        Songs(None, None, None, None, originalSongId).add_spotify_info(chosenSpotifyId, chosenSpotifyPrev)

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
        userinfo = Users(None, request.form.get("userEmail")).query_table()

        if userinfo == None:
            return apology("Username or Password incorrect")

        result = check_password(userinfo['password'], request.form.get("password"))

        if result == False:
            return apology("Username or Password incorrect")

        # remember which user has logged in
        session["user_id"] = userinfo["userId"]
        session["first_name"] = userinfo["firstName"]

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

            idData = Musicals().get_Id(get_text("newMusical"))

            Songs('pending').create_song(request.form, idData, session["user_id"])

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

            Musicals('pending').create_musical(request.form, session["user_id"])

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

        userinfo = Users(None, request.form.get("userEmail")).query_table()

        if userinfo != None:
            return apology("Invalid Username")

        Users().add_user_to_db(request.form)

        userinfo = Users(None, request.form.get("userEmail")).query_table()

        session["user_id"] = userinfo['userId']
        session["first_name"] = userinfo['firstName']

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

                        Musicals('N/A', None, int(checked)).add_musical_to_db()

                elif 'deleteMusical' in request.form:
                    for checked in checking:

                        Musicals('pending', None, int(checked)).remove_musical()

            else:
                return apology("Somtething's wrong")

            songList = Songs("pending").query_table()

            musicalList = Musicals("pending").query_table()


            return render_template("review.html", songList=songList, musicalList=musicalList)
        else:
            return apology("You are not authorized to view this")
    else:
        if session["user_id"] == 1:

            songList = Songs("pending").query_table()

            musicalList = Musicals("pending").query_table()

            return render_template("review.html", songList=songList, musicalList=musicalList)
        else:
            return apology("You are not authorized to view this")

@app.route("/roles", methods=["GET"])
def roles():

    try:

        musicalId = Musicals().get_Id(request.args.get("music"))
        data = Songs("N/A").distinct_role(musicalId)

        return jsonify(data)
    except:
        return jsonify([])

@app.route("/search", methods=["GET"])
def search():
    urlstring = "%" + request.args.get("que") + "%"

    if urlstring != "%%":
        data = Musicals("N/A", urlstring).query_table()

    else:
        return jsonify([])

    try:
        return jsonify(data)
    except:
        return jsonify(username="somethings wrong")
