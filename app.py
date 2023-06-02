from flask import Flask,redirect,request
import os
from requests import post
from dotenv import load_dotenv,find_dotenv
import logging

log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)
load_dotenv(find_dotenv())

client_id = os.getenv('CLIENT_ID')
client_secret = os.getenv('CLIENT_SECRET')
redirect_uri = "http://localhost:5000/Spotify/callback"
app = Flask(__name__)


def get_access_token(auth_code: str):
    response = post(
        "https://accounts.spotify.com/api/token",
        data={
            "grant_type": "authorization_code",
            "code": auth_code,
            "redirect_uri": redirect_uri,
        },
        auth=(client_id, client_secret),
    )
    access_token = response.json()["access_token"]
    return access_token



@app.route("/Spotify/Oauth")
async def auth():
    scope = ["playlist-modify-private", "playlist-modify-public"]
    auth_url = f"https://accounts.spotify.com/authorize?response_type=code&client_id={client_id}&redirect_uri={redirect_uri}&scope={' '.join(scope)}"
    return redirect(auth_url)

@app.route("/Spotify/callback", methods=['GET'])
async def returntoken():
    return get_access_token(request.args['code'])

if __name__ == '__main__':
    app.run()
