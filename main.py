from nicegui import ui
import pandas as pd
from random import choice
from qdrant_client import QdrantClient


ui.label('Welcome!').style('color: #6E93D6; font-size: 200%; font-weight: 300')

metadata = pd.read_parquet("metadata.parquet")
artist_song = metadata['artist_song'].tolist()

collection = "music_vectors"
client = QdrantClient(
    "https://394294d5-30bb-4958-ad1a-15a3561edce5.us-east-1-0.aws.cloud.qdrant.io:6333", 
    # api_key=os.environ['QDRANT_API_KEY'],
)

# random_song = choice(artist_song)
# @ui.refreshable
# def select_ui():
#     ui.select(
#         artist_song, value=random_song, on_change=lambda e: ui.notify(e.value)
#     ).classes('w-40')

song_selection = ui.select(
    artist_song, value='Dave Van Ronk - Buckets of Rain', on_change=lambda e: ui.notify(e.value)
).classes('w-40').classes('w-96 self-center mt-24 transition-all')

# song_selection = select_ui()
# with song_selection:
song = song_selection.value.split(' - ')[-1]
get_index = metadata.loc[metadata['name'] == song, 'index'].iloc[0]

# ui.markdown(str(get_index))

song_vector = client.retrieve(
    collection_name=collection, ids=[int(get_index)], with_payload=True, with_vectors=True
)[0]


mp3 = ui.audio(song_vector.payload['urls'])
mp3.on('ended', lambda _: ui.notify('Audio playback completed'))

# ui.button(on_click=lambda: a.props(remove='muted'), icon='volume_up').props('outline')

results = client.search(
    collection_name=collection, query_vector=song_vector.vector, limit=10
)

with ui.grid(columns=4):
    for idx, result in enumerate(results):
        #     if idx % 2 == 0:
        # with ui.column():
        ui.label(f"Genre: {result.payload['genre']}")
        ui.markdown(f"Artist: {result.payload['artist']}")
        ui.markdown(f"Song name: {result.payload['name']}")
        ui.audio(result.payload['urls'])

# ui.button(on_click=lambda: a.props('muted'), icon='volume_off').props('outline')

ui.run(title='Semantic Search for Music')#.classes('w-full justify-center mt-6')