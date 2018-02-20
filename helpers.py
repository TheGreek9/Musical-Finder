import requests
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import Flask, redirect, render_template, request, session, url_for
from functools import wraps
from databaseconfig import passconfig
from flask_bcrypt import Bcrypt

app = Flask(__name__)
bcrypt = Bcrypt(app)

helpersLogger = logging.getLogger('baseLogger')
helpersLogger.setLevel(logging.ERROR)

def apology(message, subMessage="Error", title="We're Sorry", endpoint = "Endpoint", btnName = "Go Back"):
    if subMessage == "Error":
        subMessage="We have logged the issue and are working as quickly as we can to fix it. \
        Please try back again soon."

    if endpoint == "Endpoint":
        try:
            endpoint = request.endpoint
        except:
            helpersLogger.error("Unable to get endpoint in apology function")
            endpoint = "index"
    elif endpoint == "review":
        endpoint = "index"

    return render_template("error.html", title=title, message=message, subMessage=subMessage,
    endpoint=endpoint, btnName=btnName)

def check_password(hashed, candidate):
    result = bcrypt.check_password_hash(hashed, candidate)
    return result

def email_spyro(message, site):
    password = passconfig['email']

    fromaddr = "nickjackca@gmail.com"
    toaddr = "sziangos@gmail.com"
    msg = MIMEMultipart()
    msg['From'] = fromaddr
    msg['To'] = toaddr
    msg['Subject'] = "New Addition to Database"
    body = '<p>' + str(message) + ' To view, <a href="' + str(site) + '">click here</a></p>'
    msg.attach(MIMEText(body, 'html'))
    try:
        """server_ssl = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server_ssl.ehlo()
        server_ssl.login(fromaddr, password)
        server_ssl.sendmail(fromaddr, toaddr, msg.as_string())
        server_ssl.quit()"""
    except Exception:
        helpersLogger.error('Unable to send email')

def getSong(song, artist = ""):

    client_Id = passconfig['client_id']
    client_Key = passconfig['client_key']

    authReq = requests.post("https://accounts.spotify.com/api/token", data="grant_type=client_credentials",
    headers={'Content-type': 'application/x-www-form-urlencoded'}, auth=(client_Id, client_Key))

    authKey = authReq.json()

    if 'error' in authKey:
        helpersLogger.error('Error Spotify Authentication: %s', authKey['error'])
        return -1

    authHead = {"Authorization": "Bearer " + authKey['access_token'], 'Content-type': 'application/json'}

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

    if 'error' in spotifyInfo:
        helpersLogger.error("Error Spotify Track/Artist Search: %s", spotifyInfo['error']['message'])
        return -1

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
