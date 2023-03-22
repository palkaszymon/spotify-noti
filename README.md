# Notifymusic backend

## This repo contains a SAM app with the backend of the Notifymusic side project
<br>

## Project status: Up and running, check it out [here](http://18.194.38.73)
## Technologies used: AWS (Lambda, EventBridge, SAM, Secrets Manager), Python, Neo4J AuraDB, Spotify Web API
<br>

### The functionality of this code includes checking all user-followed artists newest release using the Spotify API every 6 hours (set on Amazon EventBridge). After the check all users get an e-mail containing new releases by their favorite artists (if there are any). All the data is saved on a Neo4J Graph Database instance.
<br>

### Web app code repo [here](https://github.com/palkaszymon/spotify-noti-site)