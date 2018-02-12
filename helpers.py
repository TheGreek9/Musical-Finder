import requests
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import Flask, redirect, render_template, request, session, url_for
from functools import wraps
from databaseconfig import passconfig
from flask_bcrypt import Bcrypt

app = Flask(__name__)
bcrypt = Bcrypt(app)

def apology(text):
    endpoint = request.endpoint

    if endpoint == "review":
        return render_template("incorrect.html", incorrect=text, endpoint="index")
    else:
        return render_template("incorrect.html", incorrect=text, endpoint=endpoint)

def check_password(hashed, candidate):
    result = bcrypt.check_password_hash(hashed, candidate)
    return result

def email_spyro():
    password = passconfig['email']

    fromaddr = "nickjackca@gmail.com"
    toaddr = "sziangos@gmail.com"
    msg = MIMEMultipart()
    msg['From'] = fromaddr
    msg['To'] = toaddr
    msg['Subject'] = "New Addition to Database"
    body = '<p>There\'s a new addition to the database. To view, <a href="http://thegreek9.pythonanywhere.com/login?next=review">login here</a></p>'
    msg.attach(MIMEText(body, 'html'))
    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login(fromaddr, password)
    server.sendmail(fromaddr, toaddr, msg.as_string())
    server.quit()

def getSong(song, artist = ""):

    client_Id = passconfig['client_id']
    client_Key = passconfig['client_key']

    authReq = requests.post("https://accounts.spotify.com/api/token", data="grant_type=client_credentials",
        headers={'Content-type': 'application/x-www-form-urlencoded'}, auth=(client_Id, client_Key))

    authKey = authReq.json()['access_token']

    authHead = {"Authorization": "Bearer " + authKey, 'Content-type': 'application/json'}

    trackSearch = song.replace(" ","%20")
    if artist:
        artistSearch = artist.replace(" ","%20")
        urlSearch = "https://api.spotify.com/v1/search?q=track:" + \
        trackSearch + "%20artist:" + artistSearch + "&type=track"
    else:
        urlSearch = "https://api.spotify.com/v1/search?q=track:" + \
        trackSearch + "&type=track"

    spotifyInfo = requests.get(urlSearch, headers=authHead)
    spotifyInfo = spotifyInfo.json()

    spotifyDict = []

    i = 1
    for item in spotifyInfo.get('tracks').get('items'):
        spotifyItem = {}
        spotifyItem['num'] = i
        spotifyItem['track'] = item.get('name')
        spotifyItem['artist'] = item.get('artists')[0].get('name')
        spotifyItem['album'] = item.get('album').get('name')
        spotifyItem['id'] = item.get('id')
        spotifyItem['preview'] = item.get('preview_url')
        spotifyDict.append(spotifyItem)
        i += 1

    return spotifyDict

def get_text(text):
    return request.form.get(text)

def hash_password(password):
        hashed = bcrypt.generate_password_hash(password)
        hashed = hashed.decode('utf-8')
        return hashed

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect(url_for("login", next=request.endpoint))
        return f(*args, **kwargs)
    return decorated_function

def redirect_dest(fallback):
    dest = request.args.get("next")
    try:
        dest_url = url_for(dest)
    except:
        return redirect(url_for(fallback))
    return redirect(dest_url)
