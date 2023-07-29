from nicegui import ui
import pandas as pd
from random import choice
from qdrant_client import QdrantClient
from qdrant_client import models
import asyncio
from typing import Callable, Optional

(
    ui.label('🎧 Music Search with Qdrant')
      .style('color: #ab003c; font-size: 350%; font-weight: 450')
      .classes('self-center')
)
ui.markdown("## 🎻 A New Way to Find Music 🎶").classes('self-center')
ui.markdown(
    """
    The purpose of this app is to help creative people explore the possibilities vector databases 
    can bring to the music industry. Not only can you search for your favorite songs, but you can 
    also add filters to your search or use different collections of tunes for different purposes, 
    for example, to add every tune, beat and sound you create and search for it later when you come 
    up with new music.  

    The dataset used for this model is the [Ludwig Music Dataset (Moods and Subgenres)](https://www.kaggle.com/datasets/jorgeruizdev/ludwig-music-dataset-moods-and-subgenres). 
    You can evaluate the semantic search capabilities of our app by searching for songs you know and retrieving the 
    10 most similar one, or you can bring your own songs and compare them to those in our database. :cool:
    """
).style("max-width: 1000px").classes('self-center')


metadata = pd.read_parquet("metadata.parquet")
artist_song = sorted(metadata['artist_song'].tolist())

collection = "music_vectors"
client = QdrantClient(
    "https://394294d5-30bb-4958-ad1a-15a3561edce5.us-east-1-0.aws.cloud.qdrant.io:6333", 
    api_key=os.environ['QDRANT_API_KEY'],
)


def get_vectors():
    song = song_selection.value.split(' - ')[-1]
    get_index = metadata.loc[metadata['name'] == song, 'index'].iloc[0]
    song_vector = client.retrieve(
        collection_name=collection, ids=[int(get_index)], with_payload=True, with_vectors=True
    )

    main_artist.clear()

    with main_artist:
        ui.audio(song_vector[0].payload['urls'])

    results.clear()


    with results:
        if filters.value:
            genre_filter = models.Filter(
                must=[models.FieldCondition(key="genre", match=models.MatchValue(value=filters.value))]
            )
            music = client.search(
                collection_name=collection, query_vector=song_vector[0].vector, query_filter=genre_filter, limit=num_songs.value
            )
        else:
            music = client.search(collection_name=collection, query_vector=song_vector[0].vector, limit=num_songs.value)

        for song in music:
            with ui.column():
                with ui.card().tight().style("min-height: 260px; max-height: 300px; width: 300px"):
                    ui.image('https://picsum.photos/id/684/640/360')
                    with ui.card_section():
                        ui.label(f"Artist: {song.payload['artist']}")
                        ui.label(f"Song Name: {song.payload['name']}")
                        ui.label(f"Genre: {song.payload['genre']}")
                mp3 = ui.audio(song.payload['urls'])#.classes('w-64'):
                mp3.on('ended', lambda _: ui.notify('Audio playback completed!'))

with ui.label("How many songs would you like to get back? 🤔").classes('w-200 self-center mt-10'):
    num_songs = ui.slider(min=1, max=30, step=1, value=10)
    ui.linear_progress().bind_value_from(num_songs, 'value')

with ui.label("Filters you can apply to your search 🔎").classes('w-200 self-center mt-5'):
    filters = ui.radio([None] + metadata.genre.unique().tolist(), value=None).props('inline color=green')

song_selection = ui.select(
    artist_song, value='Dave Van Ronk - Buckets of Rain', on_change=get_vectors
).style("width: 700px").classes('w-200 self-center mt-20 transition-all')

main_artist = ui.row().classes('w-full justify-center')

results = ui.row().classes('w-full justify-center')



# dark = ui.dark_mode()
# # ui.switch(on_change=dark.enable).bind_value(dark, 'value')
# ui.button(
#     on_click=dark.enable, 
#     icon='light_mode'
# ).style("position: absolute; top: 10px; right: 10px;")

ui.run(
    title='Qdrant for Music',
    favicon='https://avatars.githubusercontent.com/u/73504361?s=280&v=4',
    dark=True
)