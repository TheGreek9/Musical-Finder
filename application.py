import os
import re
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from flask import Flask, flash, jsonify, redirect, render_template, request, url_for
from flask_jsglue import JSGlue
from cs50 import SQL
from flask_session import Session
from passlib.apps import custom_app_context as pwd_context
from tempfile import mkdtemp

from helpers import *

# configure application
app = Flask(__name__)
JSGlue(app)

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
app.config["JSONIFY_PRETTYPRINT_REGULAR"] = False
Session(app)

# configure CS50 Library to use SQLite database
db = SQL("sqlite:///musicals.db")

@app.route("/", methods=["GET", "POST"])
def index():

    if request.method == "POST":
        if get_text("musical") == "All Musicals":
            if get_text("musicalSongs") and not get_text("nonMusicalSongs"):
                songList = db.execute("SELECT musicals.musical, songs.song_title, songs.role, songs.singerArtist, songs.original_musical, songs.composer, \
                songs.genre, songs.sheet_music, songs.musicalNon FROM songs INNER JOIN musicals ON musicals.Id = songs.musicalId WHERE \
                (songs.musicalNon = 'musical' AND songs.pendingNon != 'pending')")
            elif not get_text("musicalSongs") and get_text("nonMusicalSongs"):
                songList = db.execute("SELECT musicals.musical, songs.song_title, songs.role, songs.singerArtist, songs.original_musical, songs.composer, \
                songs.genre, songs.sheet_music, songs.musicalNon FROM songs INNER JOIN musicals ON musicals.Id = songs.musicalId WHERE \
                (songs.musicalNon = 'non musical' AND songs.pendingNon != 'pending')")
            else:
                songList = db.execute("SELECT musicals.musical, songs.song_title, songs.role, songs.singerArtist, songs.original_musical, songs.composer, \
                songs.genre, songs.sheet_music, songs.musicalNon FROM songs INNER JOIN musicals ON musicals.Id = songs.musicalId WHERE songs.pendingNon != 'pending'")

            return render_template("allresults.html", songList=songList)

        else:
            music = '%' + get_text("musical") + '%'
            musicalList = db.execute("SELECT * FROM musicals WHERE musical LIKE :music", music=music)
            role = get_text("role")

            if len(musicalList) != 1:
                return render_template("searcherror.html")

            if role == "All Roles":
                if get_text("musicalSongs") and not get_text("nonMusicalSongs"):
                    songList = db.execute("SELECT * FROM songs WHERE musicalNon='musical' AND musicalId=:musicId AND pendingNon!='pending'",
                     musicId=musicalList[0]["Id"])
                elif not get_text("musicalSongs") and get_text("nonMusicalSongs"):
                    songList = db.execute("SELECT * FROM songs WHERE musicalNon='non musical'AND musicalId=:musicId AND pendingNon!='pending'",
                     musicId=musicalList[0]["Id"])
                else:
                    songList = db.execute("SELECT * FROM songs WHERE musicalId=:musicId AND pendingNon!='pending'", musicId=musicalList[0]["Id"])

                return render_template("results.html", musicalList=musicalList, songList=songList)

            else:
                if get_text("musicalSongs") and not get_text("nonMusicalSongs"):
                    songList = db.execute("SELECT * FROM songs WHERE role=:role AND musicalNon='musical' AND musicalId=:musicId AND pendingNon!='pending'",
                    role=get_text("role"), musicId=musicalList[0]["Id"])
                elif not get_text("musicalSongs") and get_text("nonMusicalSongs"):
                    songList = db.execute("SELECT * FROM songs WHERE role=:role AND musicalNon='non musical'AND musicalId=:musicId AND pendingNon!='pending'",
                    role=get_text("role"), musicId=musicalList[0]["Id"])
                else:
                    songList = db.execute("SELECT * FROM songs WHERE role=:role AND musicalId=:musicId AND pendingNon!='pending'",
                    role=get_text("role"), musicId=musicalList[0]["Id"])

                return render_template("results.html", musicalList=musicalList, songList=songList, pickedRole=role)

    else:
        return render_template("search.html")

@app.route("/changepassword", methods=["GET", "POST"])
def changepassword():

    if request.method == "POST":

        if not get_text("old password"):
            return apology("Please provide old password")

        if not get_text("new password"):
            return apology("Please provide new password")

        if not get_text("confirm password"):
            return apology("Please confirmation password")

        if get_text("new password") != get_text("confirm password"):
            return apology("New password does not match confirmation password")

        rows = db.execute("SELECT * FROM users WHERE id = :userid", userid=session["user_id"])

        if not pwd_context.verify(get_text("old password"), rows[0]["password"]):
            return apology("Invalid password")

        db.execute("UPDATE users SET password=:phash WHERE id=:userid", userid=session["user_id"], phash=pwd_context.hash(get_text("new password")))

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

        db.execute("UPDATE songs SET spotifyId=:chosenspotifyId, spotifyPrev=:chosenspotifyPrev WHERE songId=:songid",
        chosenspotifyId=chosenSpotifyId, chosenspotifyPrev=chosenSpotifyPrev, songid=originalSongId)

        return redirect(url_for('review'))

    else:

        return render_template("reviewspotify.html", spotifyDict=spotifyDict)

@app.route("/login", methods=["GET", "POST"])
def login():
# forget any user_id
    session.clear()

    # if user reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # ensure username was submitted
        if not get_text("username"):
            return apology("must provide username")

        # ensure password was submitted
        elif not get_text("password"):
            return apology("must provide password")

        # query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username", username=get_text("username"))

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
            idData = db.execute("SELECT Id FROM musicals WHERE musical=:musical", musical=get_text("newMusical"))

            db.execute("INSERT INTO songs ('musicalId', 'song_title', 'role', 'singerArtist', 'genre', 'original_musical', \
            'composer', 'musicalNon', 'sheet_music', 'pendingNon') VALUES (:musicalid, :songtitle, :role, :singerartist, \
            :genre, :original, :composer, :musicalnon, :sheet, 'pending')", musicalid=idData[0]['Id'], songtitle=get_text("songName"),
            role=get_text("role"), singerartist=get_text("singerArtist"), genre=get_text("genre"), original=get_text("originalMusical"), composer=get_text("composer"),
            musicalnon=get_text("musicalNon"), sheet=get_text("sheetMusic"))

            getSong(get_text("songName"), get_text("singerArtist"))

            #email_spyro()

            return render_template('submissionsong.html')

        elif not get_text("songName"):

            return apology("Must submit song")

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
            VALUES (:musical, :playwright, :composer, :lyricist, :genre, :production, :plot, 'pending')",
            musical=get_text("musicalName"), playwright=get_text("playwright"), composer=get_text("musicalComposer"),
            lyricist=get_text("lyricist"), genre=get_text("musicalGenre"), production=get_text("productionYear"),
            plot=get_text("plot"))

            return render_template("newmusical.html")

        elif not get_text("musicalName"):

            return apology("Must submit either musical")

        else:
            return apology("Something went wrong")
    else:

        return render_template("newmusical.html")

@app.route("/register", methods=["GET", "POST"])
def register():

    session.clear()

    if request.method == "POST":

        if not get_text("first name"):
            return apology("Must Provide Your First Name")

        if not get_text("username"):
            return apology("Must Provide A Username")

        elif not get_text("password"):
            return apology("Must Provide Password")

        elif not get_text("confirm password"):
            return apology("Must Provide Confirmation Password")

        elif get_text("password") != get_text("confirm password"):
            return apology("Password And Confirmation Password Do Not Match")

        # query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username", username=get_text("username"))

        # ensure username does not exists and password is correct
        if len(rows) != 0:
            return apology("invalid username")


        db.execute("INSERT INTO users (username, password, firstName) VALUES (:username, :phash, :firstname)",
        username=get_text("username"), phash=pwd_context.hash(get_text("password")), firstname=get_text("first name"))

        session["user_id"] = get_text("username")
        session["first_name"] = get_text("first name")

        return redirect(url_for("index"))

    else:
        return render_template("register.html")

@app.route("/review", methods=["GET", "POST"])
@login_required
def review():
    if request.method == "POST":
        if session["user_id"] == 1:
            checking = request.form.getlist("checking")

            if 'Add' in request.form:
                for checked in checking:
                    db.execute("UPDATE songs SET pendingNon='N/A' WHERE songId=:songid", songid=int(checked))


            elif 'Delete' in request.form:
                for checked in checking:
                    db.execute("DELETE FROM songs WHERE (songId=:songid AND pendingNon='pending')", songid=int(checked))


            songList = db.execute("SELECT musicals.musical, songs.songId, songs.song_title, songs.role, songs.singerArtist, songs.genre, songs.original_musical, songs.composer, \
            songs.genre, songs.sheet_music, songs.spotifyId, songs.musicalNon FROM songs INNER JOIN musicals ON musicals.Id = songs.musicalId WHERE songs.pendingNon = 'pending'")
            return render_template("review.html", songList=songList)
    else:
        if session["user_id"] == 1:
            songList = db.execute("SELECT musicals.musical, songs.songId, songs.song_title, songs.role, songs.singerArtist, songs.genre, songs.original_musical, songs.composer, \
            songs.genre, songs.sheet_music, songs.spotifyId, songs.musicalNon FROM songs INNER JOIN musicals ON musicals.Id = songs.musicalId WHERE songs.pendingNon = 'pending'")
            return render_template("review.html", songList=songList)
        else:
            return apology("You are not authorized to view this")

@app.route("/roles", methods=["GET"])
def roles():
    music = request.args.get("music")

    try:
        idData = db.execute("SELECT Id FROM musicals WHERE musical=:music", music=music)
        data = db.execute("SELECT DISTINCT role FROM songs WHERE musicalId=:musicalId AND pendingNon!='pending'", musicalId=idData[0]["Id"])

        return jsonify(data)
    except:
        return jsonify([])

@app.route("/search", methods=["GET"])
def search():
    urlstring = "%" + request.args.get("que") + "%"

    if urlstring != "%%":
        data = db.execute("SELECT * FROM musicals WHERE musical LIKE :url", url=urlstring)
    else:
        return jsonify([])

    try:
        return jsonify(data)
    except:
        return jsonify(username="hello world")
