from app import get_secret, driver
from requests import get, post
import json
from base64 import b64encode
from classes.Artist import Artist

SPOTIFY_CREDS = get_secret('spotify-api-creds')
client_id, client_secret = SPOTIFY_CREDS['CLIENT_ID'], SPOTIFY_CREDS['CLIENT_SECRET']

class Share():
    def get_oauth_token(self):
        auth_string = client_id + ':' + client_secret
        auth_b64 = str(b64encode(auth_string.encode('UTF-8')), 'UTF-8')
        url = 'https://accounts.spotify.com/api/token'
        headers = {
            "Authorization": "Basic " + auth_b64,
            "Content-Type" : "application/x-www-form-urlencoded"
        }
        data = {"grant_type": "client_credentials"}

        result = post(url, headers=headers, data=data)
        return json.loads(result.content)['access_token']

    def get_response_data(self, type):
        if type == 'playlist':
            url = f"https://api.spotify.com/v1/playlists/{self.id}?market=PL"
        elif type == 'artist':
            url = f"https://api.spotify.com/v1/artists/{self.id}/albums?include_groups=album%2Csingle&market=PL"
        response = get(url, data=None, headers={
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.get_oauth_token()}"
        })
        return response.json()
    
    def neo_write(object, id_list, firstrun=False):
        new = []
        id_list = id_list
        with driver.session() as session:
            for id in id_list:
                current = object(id)
                for item in current.get_final_items():
                    try:
                        tx = session.execute_write(current.create_item, item)
                        if firstrun == False:
                            check = tx[1].counters.nodes_created
                            if check != 0:
                                new.append(item)
                                if object == Artist:
                                    session.execute_write(current.delete_oldest, item)
                    except Exception as e:
                        print(e)
        return new
