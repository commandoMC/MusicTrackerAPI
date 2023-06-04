import base64

from flask import Flask, redirect, request, make_response
import os
import json
from requests import post, get, codes, exceptions
from dotenv import load_dotenv, find_dotenv
import logging

# log = logging.getLogger('werkzeug')
# log.setLevel(logging.ERROR)
load_dotenv(find_dotenv())

client_id = os.getenv('CLIENT_ID')
client_secret = os.getenv('CLIENT_SECRET')
redirect_uri = "https://mcapi.zortos.me/Spotify/callback"
tokenEndpoint = "https://accounts.spotify.com/api/token"
app = Flask(__name__)


def addToSpotifyData(uuid, JSON):
    try:
        # Step 1: Read the existing JSON data
        scriptPath = os.path.dirname(os.path.abspath(__file__))

        # Step 2: Create the JSON file path
        jsonFilePath = os.path.join(scriptPath, "data.json")

        try:
            with open(jsonFilePath, "r") as file:
                jsonData = file.read()
        except FileNotFoundError:
            # File doesn't exist, create it
            with open(jsonFilePath, "w") as file:
                file.write("{}")
                jsonData = "{}"

        # Step 2: Parse the JSON data
        try:
            jsonContent = json.loads(jsonData)
        except json.JSONDecodeError as e:
            print(e)
            jsonContent = {}

        spotify = jsonContent.get("spotify")
        if spotify is None:
            spotify = {}
            jsonContent["spotify"] = spotify

        # Step 3: Modify the object by adding new data
        spotify[str(uuid)] = {
            'token': JSON['access_token'],
            'refresh_token': JSON['refresh_token']
        }

        # Step 4: Write the modified object back to the JSON file
        with open(jsonFilePath, "w") as file:
            file.write(json.dumps(jsonContent))
    except IOError as e:
        print(e)


def get_access_token(auth_code: str):
    authString = client_id + ":" + client_secret
    encodedAuth = base64.b64encode(authString.encode('utf-8')).decode('utf-8')
    authHeader = "Basic " + encodedAuth

    headers = {
        "Authorization": authHeader,
        "Content-Type": "application/x-www-form-urlencoded"
    }

    body = {
        "grant_type": "authorization_code",
        "code": auth_code,
        "redirect_uri": redirect_uri
    }

    response = post(tokenEndpoint, headers=headers, data=body)

    return response.json()


def isOAuthValid(token):
    try:
        url = "https://api.spotify.com/v1/me/player/currently-playing"

        headers = {
            "Authorization": "Bearer " + token
        }
        response = get(url, headers=headers)
        responseCode = response.status_code
        if responseCode == codes.ok:
            return True
        elif responseCode == 204:
            return True
        elif responseCode == codes.unauthorized:
            return False
        else:
            # Handle other error responses
            return False
    except exceptions.RequestException as e:
        print(e)
        return False





def gettokenuuid(uuid):
    try:
        # Step 1: Get the path of the current Python script
        scriptPath = os.path.dirname(os.path.abspath(__file__))

        # Step 2: Create the JSON file path
        jsonFilePath = os.path.join(scriptPath, "data.json")

        # Step 3: Read the existing JSON data or create a new empty object
        try:
            with open(jsonFilePath, "r") as file:
                jsonData = file.read()
        except FileNotFoundError:
            return ""

        # Step 4: Parse the JSON data
        try:
            jsonContent = json.loads(jsonData)
        except json.JSONDecodeError as e:
            print(e)
            return ""

        spotify = jsonContent.get("spotify")
        if spotify is None:
            return ""

        tokenData = spotify.get(str(uuid))
        if tokenData is None:
            return ""

        return tokenData['token']
    except IOError as e:
        print(e)
        return ""


def getrefreshtokenuuid(uuid):
    try:
        # Step 1: Get the path of the current Python script
        scriptPath = os.path.dirname(os.path.abspath(__file__))

        # Step 2: Create the JSON file path
        jsonFilePath = os.path.join(scriptPath, "data.json")

        # Step 3: Read the existing JSON data or create a new empty object
        try:
            with open(jsonFilePath, "r") as file:
                jsonData = file.read()
        except FileNotFoundError:
            return None

        # Step 4: Parse the JSON data
        try:
            jsonContent = json.loads(jsonData)
        except json.JSONDecodeError as e:
            print(e)
            return None

        spotify = jsonContent.get("spotify")
        if spotify is None:
            return None

        tokenData = spotify.get(str(uuid))
        if tokenData is None:
            return None

        return tokenData['refresh_token']

    except IOError as e:
        print(e)
        return None


def check_uuid(uuid):
    try:
        # Read the JSON file
        with open("data.json", "r") as file:
            json_data = json.load(file)

        # Check if the UUID exists in the JSON data
        if uuid in json_data['spotify']:
            return True
        else:
            return False
    except FileNotFoundError:
        return False



@app.route("/Spotify/Checkuser/<uuid>")
def check_user(uuid):
    if (check_uuid(uuid)):
        return "Exists",200
    else:
        return "Not exists",401


@app.route("/Spotify/Checktoken/<UUID>")
async def CheckToken(UUID):
    if (isOAuthValid(gettokenuuid(UUID))):
        return "OK",200
    else:
        return "Expired",401

@app.route("/Spotify/Songplaying/<UUID>")
async def songplaying(UUID):
    token = gettokenuuid(UUID)
    print("GOT TOKEN" + token)
    if isOAuthValid(token):
        try:
            url = "https://api.spotify.com/v1/me/player/currently-playing"

            headers = {
                "Authorization": "Bearer " + token
            }
            print("Authorization: Bearer " + token)
            response = get(url, headers=headers)
            responseCode = response.status_code
            if responseCode == codes.ok:

                # Successfully retrieved current playing track
                return response.text
            elif responseCode == codes.unauthorized:
                # Access token is invalid or expired
                return False
            else:
                # Handle other error responses
                return False

        except exceptions.RequestException as e:
            print(e)
            return False
    else:
        return codes.unauthorized
    # TODO : refresh Token


@app.route("/Spotify/Oauth/<UUID>")
async def auth(UUID):
    scope = ["user-read-currently-playing", "user-read-playback-position"]
    auth_url = f"https://accounts.spotify.com/authorize?response_type=code&client_id={client_id}&redirect_uri={redirect_uri}&scope={' '.join(scope)}"
    resp = make_response(redirect(auth_url))
    resp.set_cookie('UUID', UUID)
    return resp


@app.route("/Spotify/refreshToken/<UUID>")
async def refreshtoken(UUID):
    authString = client_id + ":" + client_secret
    encodedAuth = base64.b64encode(authString.encode('utf-8')).decode('utf-8')
    authHeader = "Basic " + encodedAuth

    headers = {
        "Authorization": authHeader,
        "Content-Type": "application/x-www-form-urlencoded"
    }

    body = {
        "grant_type": "refresh_token",
        "refresh_token": getrefreshtokenuuid(UUID),
    }

    response = post(tokenEndpoint, headers=headers, data=body)

    return response.json()



@app.route("/Spotify/callback", methods=['GET'])
async def callback():
    responsejson = get_access_token(request.args['code'])
    try:
        if isOAuthValid(responsejson['access_token']):
            addToSpotifyData(request.cookies.get('UUID'), responsejson)
            return "Successfully Authenticated you can now return to minecraft"
        else:
            return "An error accorded try again later"
    except KeyError:
        return "An error accorded try again later"


if __name__ == '__main__':
    app.run(port=5050)
