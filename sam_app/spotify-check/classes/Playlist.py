from classes.Share import Share

class Playlist(Share):   
    def __init__(self, id):
        self.id=id
        self.response = self.get_response_data('playlist')

    def get_artist_list(self, track_id):
        return [{'artist_name': item['track']['artists'][i]['name'], 'artist_id': item['track']['artists'][i]['id']} for item in self.response['tracks']['items'] for i in range(len(item['track']['artists'])) if item['track']['id'] == track_id]

    def get_playlist_name(self):
        return self.response['name']

    def get_final_items(self):
        track_list = [{'id': item['track']['id'], 'name': item['track']['name'], 'artists': self.get_artist_list(item['track']['id'])} for item in self.response['tracks']['items']]
        return track_list
    
    def create_item(self, tx, track):
        result = tx.run(
"""
MERGE (p:Playlist {playlist_id: $playlist_id})
MERGE (t:Track {name: $name, id: $id})
WITH $artist_list as x
UNWIND x as l
MERGE (a:Artist {artist_name: l.artist_name, artist_id: l.artist_id})
WITH l
MATCH (a:Artist {artist_id: l.artist_id}), (t:Track {id: $id}), (p:Playlist {playlist_id: $playlist_id})
MERGE (t)-[:SONG_OF]->(a)
MERGE (t)-[:APPEARS_ON]->(p)
""",
    id=track['id'], name=track['name'], artist_list=track['artists'], playlist_id=self.id
    )
        summary = result.consume()
        return result, summary