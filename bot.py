import re
import configparser

import praw
import spotipy
import spotipy.util as util
import requests

from requests.exceptions import HTTPError
from pprint import pprint

def parse_title_for_song_detail(title):
    """Get song detail from submission title."""
    # r/music posts should include the artist name, song name, and genre in the
    # following format:
    #
    # <artist name> - <song name> [genre]
    pattern = re.compile(pattern=r"(.*)\s-\s(.*)\s?(\[.*\])")

    # search title for pattern
    match = pattern.search(title)
    if match:
        return {
            'artist': match.group(1).rstrip().replace('"', ''),
            'name': match.group(2).rstrip().replace('"', ''),
            'genre': match.group(3).rstrip().replace('"', ''),
            'title': title.rstrip().replace('"', ''),
        }
    
    return None

def main(n=10):
    # User-Agent string should be something unique and descriptive, including the
    # target platform, a unique application identifier, a version string, and your
    # username as contact information, in the following format:
    #
    # <platform>:<app ID>:<version string> (by /u/<reddit username>)
    user_agent = "python:r/music playlist generator:v0.0.1 (by /u/zrluety"

    # create Reddit object
    r = praw.Reddit(user_agent=user_agent,
                    site_name='MUSIC_BOT')

    subreddit = r.subreddit('music')
    songs = []
    
    # iterate through hot submissions to create a list of n songs
    for submission in subreddit.hot():
        title = submission.title

        # get song info from posts
        song = parse_title_for_song_detail(title)
        if song:
            songs.append(song)
        
        if len(songs) >= n:
            break

    spotify_config = configparser.ConfigParser()
    spotify_config.read('config.ini')

    token = util.prompt_for_user_token(
        username='Zachary Luety',
        scope='playlist-modify-public',
        client_id=spotify_config['SPOTIFY']['client_id'],
        client_secret=spotify_config['SPOTIFY']['secret'],
        redirect_uri='http://localhost/'
    )

    # create Spotify object
    spotify = spotipy.Spotify(auth=token)

    tracks = []
    for song in songs:
        # search for the track
        result = spotify.search(q=song.get('name'), limit=1)

        # get the track id
        try:
            track = result.get('tracks').get('items')[0].get('id')
            tracks.append(track)
        except HTTPError:
            continue

    # get playlists
    playlist = spotify.user_playlist_add_tracks(
        user=spotify_config['SPOTIFY']['user_id'],
        playlist_id=spotify_config['SPOTIFY']['playlist_id'],
        tracks=tracks
    )

if __name__ == '__main__':
    main()