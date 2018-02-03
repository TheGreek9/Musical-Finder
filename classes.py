import MySQLdb
from flaskext.mysql import MySQL

mysql = MySQL()

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

    def create_song(self, request, musicalId, userId):
        Songs.params['musicalId'] = musicalId
        Songs.parmas['userId'] = userId
        Songs.params['song_title'] = request.get("songName")
        Songs.params['role'] = request.get("role")
        Songs.params['singer'] = request.get("singer")
        Songs.params['artist'] = request.get("artist")
        Songs.params['genre'] = request.get("genre")
        Songs.params['originalMusical'] = request.get("originalMusical")
        Songs.params['composer'] = request.get("composer")
        Songs.params['musicalNon'] = request.get("musicalNon")
        Songs.params['sheetMusic'] = request.get("sheetMusic")

        query = "INSERT INTO songs (musicalId, userId, song_title, role, singer, artist, genre, original_musical, \
            composer, musicalNon, sheet_music, pendingNon) VALUES (%(musicalId)s, %(userId)s, %(song_title)s, %(role)s, \
            %(singer)s, %(artist)s, %(genre)s, %(originalMusical)s, %(composer)s, %(musicalNon)s, %(sheetMusic)s, %(pendingNon)s)"

        conn = MySQLdb.connect(**config)
        db = conn.cursor()
        db.execute(query, Songs.params)
        conn.commit()

    def add_song_to_db(self):
        Songs.params['songId'] = self.songId
        conn = MySQLdb.connect(**config)
        db = conn.cursor()
        db.execute("UPDATE songs SET pendingNon=%(pendingNon)s WHERE songId=%(songId)s", Songs.params)
        conn.commit()

    def remove_song(self):
        Songs.params['songId'] = self.songId
        conn = MySQLdb.connect(**config)
        db = conn.cursor()
        db.execute("DELETE FROM songs WHERE (songId=%(songId)s AND pendingNon=%(pendingNon)s)", Songs.params)
        conn.commit()

    def distinct_role(self, music):
        conn = MySQLdb.connect(**config)
        db = conn.cursor(MySQLdb.cursors.DictCursor)

        db.execute("SELECT Id FROM musicals WHERE musical = %s", [music])
        idData = db.fetchall()

        Songs.params['musicalId'] = idData[0]['Id']

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



