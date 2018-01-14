import requests
import os.path
from requests.auth import HTTPBasicAuth
from flask import redirect, render_template, request, session, url_for
from functools import wraps

def apology(text):
    endpoint = request.endpoint

    if endpoint == "review":
        return render_template("incorrect.html", incorrect=text, endpoint="index")
    else:
        return render_template("incorrect.html", incorrect=text, endpoint=endpoint)

def getSong(song, artist = ""):

    password = get_passwords()

    client_Id = password[3]
    client_Key = password[5]

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

def login_required(f):
    """
    Decorate routes to require login.

    http://flask.pocoo.org/docs/0.12/patterns/viewdecorators/
    """
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

def email_spyro():
    password = get_passwords()
    password = password[1]

    fromaddr = "nickjackca@gmail.com"
    toaddr = "sziangos@gmail.com"
    msg = MIMEMultipart()
    msg['From'] = fromaddr
    msg['To'] = toaddr
    msg['Subject'] = "New Addition to Database"
    body = '<p>There\'s a new addition to the database. To view, <a href="www.google.com">login here</a></p>'
    msg.attach(MIMEText(body, 'html'))
    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login(fromaddr, password)
    server.sendmail(fromaddr, toaddr, msg.as_string())
    server.quit()

def get_passwords():
    text=[]
    with open('pass.txt', 'r') as file:
        for line in file.readlines():
            text.append(line.rstrip('\n'))

    return text
