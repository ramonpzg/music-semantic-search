from qdrant_client import QdrantClient, models
from nicegui import ui
import pandas as pd
import os


(
    ui.label('🎧 Music Search with Qdrant')
      .style('color: #ab003c; font-size: 350%; font-weight: 450')
      .classes('self-center')
)

ui.markdown("## 🎻 A New Way to Find Music 🎶").classes('self-center')
ui.markdown(
    """
    🎯 **The purpose** of this app is to showcase one of the many (cool 😎 and fun 💃🏻🕺🏽) ways in which you can use [Qdrant](https://qdrant.tech/) 
    to conduct [semantic search](https://en.wikipedia.org/wiki/Semantic_search) using music data.

    
    🥁 **The dataset** used for demo app is the [Ludwig Music Dataset (Moods and Subgenres)](https://www.kaggle.com/datasets/jorgeruizdev/ludwig-music-dataset-moods-and-subgenres) 
    which is freely available on Kaggle. I contains songs for the 9 genres shown below as well as some metadata which was 
    used as the [payload](https://qdrant.tech/documentation/concepts/payload/) for this app.

    
    🤖 **The model** used to extract the embeddings is the [`panns_inference`](https://github.com/qiuqiangkong/panns_inference) 
    freely distributed as a Python library. Please note that, while these embeddings show a remarkable quality on the Ludwig 
    data, they have been taken as is out-of-the-box and have not been fine-tuned one on the Ludwig dataset.

    You can evaluate the semantic search capabilities of our app by searching for songs you know and retrieving the 
    most similar ones. In addition, if you want to see similar songs in a different genre than the one of the song you 
    selected, pick one of the genres available below to see the results.

    💽 **The songs** returned by Qdrant are being downloaded on-the-fly from an S3 bucket.

    Each result will come back with a card containing an **image** of the artist, the **name** of the artist and the song, 
    the **similarity** score, and the **genre** of song (inconsistencies in the genre, e.g. Adele songs classified as "electronic" 
    are present in the dataset).

    🖼️ **The images** shown in the cards represent the names of each artist in the dataset (~4400 unique ones) and these were 
    collected using the first result from a query sent to Bing's Image Search API. Hence, some images might not be the correct ones.
    """
).style("max-width: 1000px; font-size: 120%").classes('self-center')


metadata = pd.read_csv("payload.csv")
artist_song = sorted(metadata['artist_song'].tolist())

collection = "music_vectors"
client = QdrantClient(
    "https://394294d5-30bb-4958-ad1a-15a3561edce5.us-east-1-0.aws.cloud.qdrant.io:6333", 
    api_key=os.environ['QDRANT_API_KEY']
)

def create_music_card(qdrant_results):
    for song in qdrant_results:
        with ui.column():
            with ui.card().tight().style("height: 350px; width: 300px"):
                ui.image(song.payload['photos']).classes('w-[300px] h-[210px]')
                with ui.card_section():
                    ui.label(f"Artist: {song.payload['artist']}")
                    ui.label(f"Song Name: {song.payload['name']}")
                    ui.label(f"Genre: {song.payload['genre']}")
                    try:
                        ui.label(f"Score: {song.score}")
                    except:
                        pass
            first_song = ui.audio(song.payload['urls'])#.classes('w-64'):
            first_song.on('ended', lambda _: ui.notify('Audio playback completed!'))


def get_vectors():
    """Callback function for our search box"""
    song = song_selection.value.split(' - ')[-1] # get the name of the song selected
    get_index = metadata.loc[metadata['name'] == song, 'index'].iloc[0] # get the index of such a song

    # retrieve the vector and metadata associated with it
    song_vector = client.retrieve(
        collection_name=collection, ids=[int(get_index)], with_payload=True, with_vectors=True
    )

    # Clear the result from the previous artist selected
    main_artist.clear()

    with main_artist:
        create_music_card(song_vector)

    # Clear the result from the previous search request
    results.clear()

    with results:
        if filters.value:
            genre_filter = models.Filter(
                must=[models.FieldCondition(key="genre", match=models.MatchValue(value=filters.value))]
            )
            music = client.search(
                collection_name=collection, query_vector=song_vector[0].vector, query_filter=genre_filter, limit=num_songs.value
            )[1:]
        else:
            music = client.search(collection_name=collection, query_vector=song_vector[0].vector, limit=num_songs.value)[1:]

        create_music_card(music)

with ui.label("How many songs would you like to get back? 🤔").classes('w-200 self-center mt-10'):
    num_songs = ui.slider(min=1, max=30, step=1, value=11)
    ui.linear_progress().bind_value_from(num_songs, 'value')

with ui.label("Filters you can apply to your search 🔎").classes('w-200 self-center mt-5'):
    filters = ui.radio([None] + metadata.genre.unique().tolist(), value=None).props('inline color=#ab003c')

song_selection = ui.select(
    artist_song, value='Dave Van Ronk - Buckets of Rain', on_change=get_vectors
).style("width: 700px").classes('w-200 self-center mt-10 transition-all')

main_artist = ui.row().classes('w-full justify-center')

results = ui.row().classes('w-full justify-center')


ui.colors(
    primary='#ab003c',
    secondary='#2c387e',
    accent='#f50057',
    dark='#f73378',
    positive='#f73378',
    negative='#ba000d'

)

ui.run(
    title='Qdrant for Music',
    favicon='https://avatars.githubusercontent.com/u/73504361?s=280&v=4',
    # dark=True
)