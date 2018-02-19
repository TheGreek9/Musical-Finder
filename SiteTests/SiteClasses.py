import MySQLdb
from flaskext.mysql import MySQL
from flask import Flask
from flask_bcrypt import Bcrypt

from helpers import apology

mysql = MySQL()
app = Flask(__name__)
bcrypt = Bcrypt(app)

config = {
    'user': 'TheGreek9',
    'password': 'oatmealcookie',
    'host': 'TheGreek9.mysql.pythonanywhere-services.com',
    'database' : 'TheGreek9$musicalsite'
}

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

    def add_song_to_db(self):
        Songs.params['songId'] = self.songId
        query = "UPDATE songs SET pendingNon=%(pendingNon)s WHERE songId=%(songId)s"

        connect_db(query, Songs.params)

    def remove_song(self):
        Songs.params['songId'] = self.songId
        query = "DELETE FROM songs WHERE (songId=%(songId)s AND pendingNon=%(pendingNon)s)"

        connect_db(query, Songs.params)

    def distinct_role(self, musicalId):
        conn = MySQLdb.connect(**config)
        db = conn.cursor(MySQLdb.cursors.DictCursor)

        Songs.params['musicalId'] = musicalId

        db.execute("SELECT DISTINCT role FROM songs WHERE musicalId=%(musicalId)s AND pendingNon=%(pendingNon)s", Songs.params)
        data = db.fetchall()
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

        conn = MySQLdb.connect(**config)
        db = conn.cursor(MySQLdb.cursors.DictCursor)
        joinedString = " ".join(Songs.querystring)

        query = "SELECT musicals.musical, songs.songId, songs.musicalId, \
        songs.userId, songs.song_title, songs.role, songs.singer, songs.artist, \
        songs.genre, songs.original_musical, songs.composer, songs.musicalNon, songs.sheet_music,\
        songs.spotifyId, songs.spotifyPrev, songs.pendingNon, songs.created\
        FROM songs INNER JOIN musicals ON musicals.Id = songs.musicalId WHERE ({})".format(joinedString)

        db.execute(query, Songs.params)
        songlist = db.fetchall()
        return songlist

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

        conn = MySQLdb.connect(**config)
        db = conn.cursor()
        db.execute(query, Musicals.params)
        musicalId = db.fetchone()

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

        conn = MySQLdb.connect(**config)
        db = conn.cursor(MySQLdb.cursors.DictCursor)
        db.execute(query, Musicals.params)
        musicalList = db.fetchall()
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

    def add_user_to_db(self, password):
        Users.query = "UPDATE users SET password=%(password)s WHERE userId=%(userId)s"
        pass

    def change_password(self, request):
        conn = MySQLdb.connect(**config)
        db = conn.cursor(MySQLdb.cursors.DictCursor)

        db.execute("SELECT * FROM users WHERE userId = %(userId)s", Users.params)
        userinfo = db.fetchone()

        results = check_password(request.get("old password"), userinfo['password'])
        if results == False:
            apology("Invalid Credentials")

        try:
            password = bcrypt.generate_password_hash(request.get("new password"))
            Users.params['password'] = password
            query = "UPDATE users SET password=%(password)s WHERE userId=%(userId)s"
        except:
            apology("Unable to hash new password")

        connect_db(query, Users.params)

    def log_user_in(self, request):
        conn = MySQLdb.connect(**config)
        db = conn.cursor(MySQLdb.cursors.DictCursor)

        db.execute("SELECT * FROM users WHERE userEmail = %s", Users.params)

    def query_table(self):
        if self.userId is not None:
            Users.querystring[0] = "userId = %(userId)s"
        elif self.userEmail is not None:
            Users.querystring[0] = "userEmail = %(userEmail)s"

        joinedString = " ".join(Users.querystring)

        query = "SELECT users.userId, users.firstName, users.lastName, users.userEmail, users.password\
        FROM users WHERE {}".format(joinedString)

        conn = MySQLdb.connect(**config)
        db = conn.cursor(MySQLdb.cursors.DictCursor)
        db.execute(query, Users.params)
        userList = db.fetchall()
        return userList

def hash_password(password):
    hashed = bcrypt.generate_password(password)
    return hashed

def check_password(candidate, hashed):
    result = bcrypt.check_password_hash(hashed, candidate)
    return result

def connect_db(query, params):
    conn = MySQLdb.connect(**config)
    db = conn.cursor()
    db.execute(query, params)
    conn.commit()
