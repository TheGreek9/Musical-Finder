import os
import re
import smtplib
import MySQLdb
from flask import Flask, flash, jsonify, redirect, render_template, request, url_for, session
from flask_jsglue import JSGlue
from cs50 import SQL
from flask_session import Session
from passlib.apps import custom_app_context as pwd_context
from tempfile import mkdtemp
from flask_bcrypt import Bcrypt
from flaskext.mysql import MySQL

from helpers import apology, email_spyro, getSong, get_text, login_required, redirect_dest

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
app.config["JSONIFY_PRETTYPRINT_REGULAR"] = False

conn = MySQLdb.connect("TheGreek9.mysql.pythonanywhere-services.com","TheGreek9","oatmealcookie","TheGreek9$musicalsite")
db = conn.cursor(MySQLdb.cursors.DictCursor)

@app.route("/", methods=["GET", "POST"])
def index():

    if request.method == "POST":
        if get_text("musical") == "All Musicals":
            if get_text("musicalSongs") and not get_text("nonMusicalSongs"):
                db.execute("SELECT musicals.musical, songs.song_title, songs.role, songs.singer, songs.artist, songs.original_musical, songs.composer, \
                songs.genre, songs.sheet_music, songs.musicalNon, songs.spotifyPrev FROM songs INNER JOIN musicals ON musicals.Id = songs.musicalId WHERE \
                (songs.musicalNon = 'musical' AND songs.pendingNon != 'pending')")
                songList = db.fetchall()
            elif not get_text("musicalSongs") and get_text("nonMusicalSongs"):
                db.execute("SELECT musicals.musical, songs.song_title, songs.role, songs.singer, songs.artist, songs.original_musical, songs.composer, \
                songs.genre, songs.sheet_music, songs.musicalNon, songs.spotifyPrev FROM songs INNER JOIN musicals ON musicals.Id = songs.musicalId WHERE \
                (songs.musicalNon = 'non musical' AND songs.pendingNon != 'pending')")
                songList = db.fetchall()
            else:
                db.execute("SELECT musicals.musical, songs.song_title, songs.role, songs.singer, songs.artist, songs.original_musical, songs.composer, \
                songs.genre, songs.sheet_music, songs.musicalNon, songs.spotifyPrev FROM songs INNER JOIN musicals ON musicals.Id = songs.musicalId WHERE songs.pendingNon != 'pending'")
                songList = db.fetchall()

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
                    db.execute("SELECT * FROM songs WHERE musicalNon='musical' AND musicalId=%s AND pendingNon!='pending'",
                     [musicalList[0]["Id"]])
                    songList = db.fetchall()
                elif not get_text("musicalSongs") and get_text("nonMusicalSongs"):
                    db.execute("SELECT * FROM songs WHERE musicalNon='non musical'AND musicalId=%s AND pendingNon!='pending'",
                    [musicalList[0]["Id"]])
                    songList = db.fetchall()
                else:
                    db.execute("SELECT * FROM songs WHERE musicalId=%s AND pendingNon!='pending'", [musicalList[0]["Id"]])
                    songList = db.fetchall()

                return render_template("results.html", musicalList=musicalList, songList=songList)

            else:
                if get_text("musicalSongs") and not get_text("nonMusicalSongs"):
                    db.execute("SELECT * FROM songs WHERE role=%s AND musicalNon='musical' AND musicalId=%s AND pendingNon!='pending'",
                    [get_text("role"), musicalList[0]["Id"]])
                    songList = db.fetchall()
                elif not get_text("musicalSongs") and get_text("nonMusicalSongs"):
                    db.execute("SELECT * FROM songs WHERE role=%s AND musicalNon='non musical'AND musicalId=%s AND pendingNon!='pending'",
                    [get_text("role"), musicalList[0]["Id"]])
                    songList = db.fetchall()
                else:
                    db.execute("SELECT * FROM songs WHERE role=%s AND musicalId=%s AND pendingNon!='pending'",
                    [get_text("role"), musicalList[0]["Id"]])
                    songList = db.fetchall()

                return render_template("results.html", musicalList=musicalList, songList=songList, pickedRole=role)

    else:
        """testing = dict(test = 1, genre = "comedy")
        test = 1
        db.execute("SELECT * FROM musicals WHERE Id = %s", [test])
        rows = db.fetchall()
        print("@@@@@@@@@@@@@@@@@@@{}".format(rows[0]['Id']))"""
        return render_template("search.html")

@app.route("/changepassword", methods=["GET", "POST"])
@login_required
def changepassword():

    if request.method == "POST":

        db.execute("SELECT * FROM users WHERE id = %s", [Session["user_id"]])

        rows = db.fetchall()

        if not pwd_context.verify(get_text("old password"), rows[0]["password"]):
            return apology("Invalid password")

        db.execute("UPDATE users SET password=%s WHERE id=%s", [session["user_id"], pwd_context.hash(get_text("new password"))])

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
        db.execute("SELECT * FROM users WHERE username = %s", [get_text("username")])

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

            db.execute("INSERT INTO songs ('musicalId', 'song_title', 'role', 'singer', 'artist', 'genre', 'original_musical', \
            'composer', 'musicalNon', 'sheet_music', 'pendingNon') VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'pending')", [idData[0]['Id'], get_text("songName"),
            get_text("role"), get_text("singer"), get_text("artist"), get_text("genre"), get_text("originalMusical"), get_text("composer"),
            get_text("musicalNon"), get_text("sheetMusic")])

            getSong(get_text("songName"), get_text("artist"))

            #email_spyro()

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
            db.execute("INSERT INTO musicals ('musical', 'playwright', 'composer', 'lyricist', 'genre', 'production_year', 'plot', 'pendingNon') \
            VALUES (%s, %s, %s, %s, %s, %s, %s, 'pending')", [get_text("musicalName"), get_text("playwright"), get_text("musicalComposer"),
            get_text("lyricist"), get_text("musicalGenre"), get_text("productionYear"), get_text("plot")])

            #email_spyro()

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
        db.execute("SELECT * FROM users WHERE username = %s", [get_text("username")])

        rows = db.fetchall()

        # ensure username does not exists and password is correct
        if len(rows) != 0:
            return apology("invalid username")


        db.execute("INSERT INTO users (username, password, firstName) VALUES (%s, %s, %s)",
        [get_text("username"), pwd_context.hash(get_text("password")), get_text("first name")])

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
                        db.execute("UPDATE songs SET pendingNon='N/A' WHERE songId=%s", [int(checked)])


                elif 'deleteSong' in request.form:
                    for checked in checking:
                        db.execute("DELETE FROM songs WHERE (songId=%s AND pendingNon='pending')", [int(checked)])

            elif 'addMusical' in request.form or 'deleteMusical' in request.form:
                checking = request.form.getlist("checkingMusical")

                if 'addMusical' in request.form:
                    for checked in checking:
                        db.execute("UPDATE musicals SET pendingNon='N/A' WHERE Id=%s", [int(checked)])


                elif 'deleteMusical' in request.form:
                    for checked in checking:
                        db.execute("DELETE FROM musicals WHERE (Id=%s AND pendingNon='pending')", [int(checked)])

            else:
                return apology("Somtething's wrong")


            db.execute("SELECT musicals.musical, songs.songId, songs.song_title, songs.role, songs.singer, songs.artist, songs.genre, songs.original_musical, songs.composer, \
            songs.genre, songs.sheet_music, songs.spotifyId, songs.musicalNon FROM songs INNER JOIN musicals ON musicals.Id = songs.musicalId WHERE songs.pendingNon = 'pending'")
            songList = db.fetchall()

            db.execute("SELECT * FROM musicals WHERE pendingNon='pending'")

            musicalList = db.fetchall()

            return render_template("review.html", songList=songList)
        else:
            return apology("You are not authorized to view this")
    else:
        if session["user_id"] == 1:
            db.execute("SELECT musicals.musical, songs.songId, songs.song_title, songs.role, songs.singer, songs.artist, songs.genre, songs.original_musical, songs.composer, \
            songs.genre, songs.sheet_music, songs.spotifyId, songs.musicalNon FROM songs INNER JOIN musicals ON musicals.Id = songs.musicalId WHERE songs.pendingNon = 'pending'")

            songList = db.fetchall()

            db.execute("SELECT * FROM musicals WHERE pendingNon='pending'")

            musicalList = db.fetchall()

            return render_template("review.html", songList=songList, musicalList=musicalList)
        else:
            return apology("You are not authorized to view this")

@app.route("/roles", methods=["GET"])
def roles():
    music = request.args.get("music")

    try:
        db.execute("SELECT Id FROM musicals WHERE musical = %s", [music])
        idData = db.fetchall()
        db.execute("SELECT DISTINCT role FROM songs WHERE musicalId=%s AND pendingNon!='pending'", [idData[0]['Id']])
        data = db.fetchall()
        return jsonify(data)
    except:
        return jsonify([])

@app.route("/search", methods=["GET"])
def search():
    urlstring = "%" + request.args.get("que") + "%"

    if urlstring != "%%":
        db.execute("SELECT * FROM musicals WHERE (musical LIKE %s AND pendingNon != 'pending');", [urlstring])
        data = db.fetchall()
    else:
        return jsonify([])

    try:
        return jsonify(data)
    except:
        return jsonify(username="somethings wrong")