import MySQLdb
import logging
import logging.handlers
from flaskext.mysql import MySQL
from flask import Flask
from databaseconfig import config
from helpers import hash_password, apology, email_spyro

mysql = MySQL()

classLogger = logging.getLogger('baseLogger')
classLogger.setLevel(logging.ERROR)

def connect_db(query, params, fetch = None):
    try:
        conn = MySQLdb.connect(**config)
        db = conn.cursor(MySQLdb.cursors.DictCursor)
        db.execute(query, params)
    except Exception:
        classLogger.error('db.execute function error')
        raise

    try:
        if fetch == 1:
            return db.fetchone()
        elif fetch == 2:
            return db.fetchall()
        else:
            conn.commit()
    except Exception:
        classLogger.error('Error with db fetching functions')
        raise

def test_connection():
    try:
        conn = MySQLdb.connect(**config)
        db = conn.cursor(MySQLdb.cursors.DictCursor)
    except Exception:
        classLogger.error('Error with trying to initially connect to database')
        apology("There was a problem connecting testing")
        raise

class Songs:
    #Need to add query to string instead of append because WSGI spawns 2 threads and
    #duplicates this process, leading to a double append of string
    querystring = [""] * 4
    params = {}

    def __init__(self, pendingNon = 'N/A', musicalNon = None, musicalId = None, role = None, songId = None):
        self.pendingNon = pendingNon
        Songs.params['pendingNon'] = self.pendingNon
        self.musicalNon = musicalNon
        self.musicalId = musicalId
        self.role = role
        self.songId = songId

    def add_song_to_db(self):
        Songs.params['songId'] = self.songId
        query = "UPDATE songs SET pendingNon=%(pendingNon)s WHERE songId=%(songId)s"

        connect_db(query, Songs.params)

    def add_spotify_info(self, spotifyId, spotifyPrev):
        Songs.params['songId'] = self.songId
        Songs.params['spotifyId'] = spotifyId
        Songs.params['spotifyPrev'] = spotifyPrev

        query = "UPDATE songs SET spotifyId=%(spotifyId)s, spotifyPrev=%(spotifyPrev)s WHERE songId=%(songId)s"

        connect_db(query, Songs.params)

    def create_song(self, request, userId, musicalId):
        Songs.params['userId'] = userId
        Songs.params['musicalId'] = musicalId
        Songs.params['song_title'] = request.get("songName")
        Songs.params['role'] = request.get("role")
        Songs.params['singer'] = request.get("singer")
        Songs.params['artist'] = request.get("artist")
        Songs.params['genre'] = request.get("genre")
        Songs.params['originalMusical'] = request.get("originalMusical")
        Songs.params['composer'] = request.get("composer")
        Songs.params['musicalNon'] = request.get("musicalNon")
        Songs.params['sheetMusic'] = request.get("sheetMusic")

        query = "INSERT INTO songs (userId, musicalId, song_title, role, singer, artist, genre, original_musical, \
            composer, musicalNon, sheet_music, pendingNon) VALUES (%(userId)s, %(musicalId)s, %(song_title)s, %(role)s, \
            %(singer)s, %(artist)s, %(genre)s, %(originalMusical)s, %(composer)s, %(musicalNon)s, %(sheetMusic)s, %(pendingNon)s)"

        connect_db(query, Songs.params)

    def distinct_role(self, musicalId):
        conn = MySQLdb.connect(**config)
        db = conn.cursor(MySQLdb.cursors.DictCursor)

        Songs.params['musicalId'] = musicalId

        query = "SELECT DISTINCT role FROM songs WHERE musicalId=%(musicalId)s AND pendingNon=%(pendingNon)s"
        data = connect_db(query, Songs.params, 2)
        return data

    def query_table(self):
        Songs.querystring[0] = "songs.pendingNon = %(pendingNon)s"

        if self.musicalNon is not None:
             Songs.params['musicalNon'] = self.musicalNon
             Songs.querystring[1] = " AND songs.musicalNon = %(musicalNon)s"

        if self.musicalId is not None:
            Songs.params['musicalId'] = self.musicalId
            Songs.querystring[2] = " AND songs.musicalId = %(musicalId)s"

        if self.role is not None:
            Songs.params['role'] = self.role
            Songs.querystring[3] = " AND songs.role = %(role)s"

        joinedString = " ".join(Songs.querystring)

        query = "SELECT musicals.musical, songs.songId, songs.musicalId, \
        songs.userId, songs.song_title, songs.role, songs.singer, songs.artist, \
        songs.genre, songs.original_musical, songs.composer, songs.musicalNon, songs.sheet_music,\
        songs.spotifyId, songs.spotifyPrev, songs.pendingNon, songs.created\
        FROM songs INNER JOIN musicals ON musicals.Id = songs.musicalId WHERE ({})".format(joinedString)

        songList = connect_db(query, Songs.params, 2)
        return songList

    def remove_song(self):
        Songs.params['songId'] = self.songId
        query = "DELETE FROM songs WHERE (songId=%(songId)s AND pendingNon=%(pendingNon)s)"

        connect_db(query, Songs.params)

class Musicals:
    #Need to add query to string instead of append because WSGI spawns 2 threads and
    #duplicates this process, leading to a double append of string
    querystring = [""] * 3
    params = {}

    def __init__(self, pendingNon = 'N/A', musical = None, Id = None):
        self.pendingNon = pendingNon
        Musicals.params['pendingNon'] = self.pendingNon
        self.musical = musical
        self.Id = Id

    def create_musical(self, request, userId):
        Musicals.params['userId'] = userId
        Musicals.params['musical'] = request.get("musicalName")
        Musicals.params['playwright'] = request.get("playwright")
        Musicals.params['composer'] = request.get("musicalComposer")
        Musicals.params['lyricist'] = request.get("lyricist")
        Musicals.params['genre'] = request.get("musicalGenre")
        Musicals.params['production_year'] = request.get("productionYear")
        Musicals.params['plot'] = request.get("plot")

        query = "INSERT INTO musicals (userId, musical, playwright, composer, lyricist, genre, production_year, plot, pendingNon) \
                    VALUES (%(userId)s, %(musical)s, %(playwright)s, %(composer)s, %(lyricist)s, %(genre)s, %(production_year)s, %(plot)s,%(pendingNon)s)"

        connect_db(query, Musicals.params)

    def add_musical_to_db(self):
        Musicals.params['Id'] = self.Id
        query = "UPDATE musicals SET pendingNon=%(pendingNon)s WHERE Id=%(Id)s"

        connect_db(query, Musicals.params)

    def get_Id(self, musicalName):
        Musicals.params['musical'] = musicalName
        query = "SELECT Id FROM musicals WHERE musical=%(musical)s"

        musicalId = connect_db(query, Musicals.params, 1)
        return musicalId

    def remove_musical(self):
        Musicals.params['Id'] = self.Id
        query = "DELETE FROM musicals WHERE (Id=%(Id)s AND pendingNon=%(pendingNon)s)"

        connect_db(query, Musicals.params)

    def query_table(self):
        Musicals.querystring[0] = "musicals.pendingNon = %(pendingNon)s"

        if self.musical is not None:
             Musicals.params['musical'] = self.musical
             Musicals.querystring[1] = " AND musicals.musical LIKE %(musical)s"

        if self.Id is not None:
            Musicals.params['Id'] = self.Id
            Musicals.querystring[2] = " AND musicals.Id = %(Id)s"

        joinedString = " ".join(Musicals.querystring)

        query = "SELECT musicals.Id, musicals.userId, musicals.musical, musicals.playwright, musicals.composer, \
        musicals.lyricist, musicals.genre, musicals.production_year, musicals.plot, musicals.pendingNon, musicals.created\
        FROM musicals WHERE ({})".format(joinedString)

        musicalList = connect_db(query, Musicals.params, 2)
        return musicalList

class Users:

    querystring = [""]
    params = {}

    def __init__(self, userId = None, userEmail = None):
        self.userId = userId
        self.userEmail = userEmail

        if self.userId is not None:
            Users.params['userId'] = self.userId
        elif self.userEmail is not None:
            Users.params['userEmail'] = self.userEmail

    def add_user_to_db(self, request):
        Users.params['firstName'] = request.get("firstName")
        Users.params['lastName'] = request.get("lastName")
        Users.params['userEmail'] = request.get("userEmail")
        password = hash_password(request.get("password"))
        Users.params['password'] = password

        query = "INSERT INTO users (firstName, lastName, userEmail, password) \
        VALUES (%(firstName)s, %(lastName)s, %(userEmail)s, %(password)s)"

        connect_db(query, Users.params)

    def change_password(self, password):
        Users.params['password'] = password

        query = "UPDATE users SET password=%(password)s WHERE userId=%(userId)s"

        connect_db(query, Users.params)

    def query_table(self):
        if self.userId is not None:
            Users.querystring[0] = "userId = %(userId)s"
        elif self.userEmail is not None:
            Users.querystring[0] = "userEmail = %(userEmail)s"

        joinedString = " ".join(Users.querystring)

        query = "SELECT users.userId, users.firstName, users.lastName, users.userEmail, users.password\
        FROM users WHERE {}".format(joinedString)

        userList = connect_db(query, Users.params, 1)
        return userList

class GMailHandler(logging.Handler):
    def emit(self, record):
        record = self.format(record)
        try:
            email_spyro(record, "#")
        except:
            raise
