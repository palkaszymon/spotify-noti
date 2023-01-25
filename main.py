import json
from shared_func import Share

playlist_ids = ['6jb23MIDO80GqVaNIsyUfO', '4wWGESRiQIVhFrabk4RwJA', '5037GRVTAdYiQvGRpzWIDT', '7ep8g0ewFtEKjhgwmFy957']

class Playlist(Share):  
    def __init__(self, id):
        self.id=id
        self.response = self.get_response_data()

    def get_playlist_name(self):
        return self.response['name']

    def get_playlist_items(self):
        id_list = [item['track']['id'] for item in self.response['tracks']['items']]
        with open('list.json', 'w') as f:
            json.dump(id_list, f)
        return id_list

    def playlist_new_songs(self):
        with open(f'playlists/{self.id}.json', 'r') as f:
            old_list = json.load(f)
            new_list = self.get_playlist_items()
        return [song for song in new_list if song not in old_list]

    def save_playlist_songs(self):
        # will be database (maybe neo4j) for now in file
        with open(f'playlists/{self.id}.json', 'w') as f:
            json.dump(self.get_playlist_items(), f)

for id in playlist_ids:
    Playlist(id).save_playlist_songs()