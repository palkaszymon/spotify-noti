from classes.Share import Share
from app import driver
from datetime import datetime

class Artist(Share):
    def __init__(self, id):
        self.id=id
        self.response = self.get_response_data('artist')
    
    def get_artist_list(self, track_id):
        return [{'artist_name': item['artists'][i]['name'], 'artist_id': item['artists'][i]['id']} for item in self.response['items'] for i in range(len(item['artists'])) if item['id'] == track_id]
    
    def get_items(self):
        return [{'id': item['id'], 'name': item['name'], 'type': item['album_type'], 'artists': self.get_artist_list(item['id']), 'release_date': item['release_date']} for item in self.response['items']]
    
    # Sorts the albums by release date descending, and returns the newest 3
    def get_final_items(self):
        albums = sorted(self.get_items(), key = lambda x: datetime.strptime(self.check_date(x['release_date']), '%Y-%m-%d'), reverse=True)
        if len(albums) != 2:
            filter_dupes =  [albums[i] for i in range(len(albums)-1) if albums[i]['name'] != albums[i+1]['name']][:3]
        else:
            if albums[0]['name'] != albums[1]['name']:
                filter_dupes = albums[:2]
            else:
                filter_dupes = albums[:1]
        return filter_dupes

    @staticmethod
    def create_item(tx, album):
        result = tx.run(
"""
MERGE (al:Album {name: $name, type: $type, release_date: $release_date, id: $id})
WITH $artist_list as x
UNWIND x as l
MERGE (a:Artist {artist_name: l.artist_name, artist_id: l.artist_id})
WITH l
MATCH (a:Artist {artist_id: l.artist_id}), (al:Album {id: $id})
MERGE (al)-[:ALBUM_OF]->(a)
""",
    name=album['name'], type=album['type'], release_date= album['release_date'], id=album['id'], artist_list=album['artists']
    )
        summary = result.consume()
        return result, summary
    
    @staticmethod
    def delete_oldest(tx, album):
        result = tx.run(
"""
MATCH (al:Album)--(a:Artist {artist_id: $artist_id})
WITH min(al.release_date) as min
MATCH (al:Album) WHERE al.release_date = min
DETACH DELETE al
""",
    artist_id=album['artists'][0]['artist_id']
    )
        return result
    
    @staticmethod
    def get_all_artists(tx):
        result = tx.run(
"""
MATCH (a:Artist)
RETURN a.artist_id
""")
        return [record.value() for record in result]
