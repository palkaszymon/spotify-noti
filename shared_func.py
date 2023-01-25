import requests
from oauth import get_oauth_token

class Share():
    def get_response_data(self):
        url = f"https://api.spotify.com/v1/playlists/{self.id}?market=PL"
        response = requests.get(url, data=None, headers={
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": f"Bearer {get_oauth_token()}"
        })
        return response.json()

    def get_track_name(self, id):
        return str([item['track']['name']for item in self.response['tracks']['items']if item['track']['id'] == id][0])

    def get_artist_list(self, track_id):
        return [item['track']['artists'][i]['name'] for item in self.response['tracks']['items'] for i in range(len(item['track']['artists'])) if item['track']['id'] == track_id]
