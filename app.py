from qdrant_client import QdrantClient
from transformers import pipeline
import streamlit as st
import pandas as pd
import tempfile
import urllib3
import librosa
import torch
import os


st.title("Semantic Search for Music")
st.subheader("A New Way to Search for your Favorite Songs Using :red[Qdrant]")
st.markdown("""
The purpose of this app is to help creative people explore the possibilities vector databases 
can bring to the music industry. Not only can you search for your favorite songs, but you can 
also add filters to your search or use different collections of tunes for different purposes, 
for example, to add every tune, beat and sound you create and search for it later when you come 
up with new music.  

The dataset used for this model is the [Ludwig Music Dataset (Moods and Subgenres)](https://www.kaggle.com/datasets/jorgeruizdev/ludwig-music-dataset-moods-and-subgenres). 
You can evaluate the semantic search capabilities of our app by searching for songs you know and retrieving the 
10 most similar one, or you can bring your own songs and compare them to those in our database. :cool:

""")

http = urllib3.PoolManager()
metadata = pd.read_parquet("metadata.parquet")
artist_song = metadata['artist_song'].sort_values().tolist()
collection = "music_vectors"
classifier = pipeline("audio-classification", model="ramonpzg/wav2musicgenre")
client     = QdrantClient(
    "https://394294d5-30bb-4958-ad1a-15a3561edce5.us-east-1-0.aws.cloud.qdrant.io:6333", 
    api_key=os.environ['QDRANT_API_KEY'],
)


options = st.selectbox(label="Select an Option", options=[None, 'Our Database', 'Your Music'], index=0)


if options == 'Our Database':
    a_song = st.selectbox(label="Songs", options=artist_song, index=0)

    song = a_song.split(' - ')[-1]
    get_index = metadata.loc[metadata['name'] == song, 'index'].iloc[0]

    song_vector = client.retrieve(
        collection_name=collection, ids=[int(get_index)], with_payload=True, with_vectors=True
    )[0]

    try:
        mp3 = st.audio(song_vector.payload['urls'])
    except:
        response = http.request('GET', song_vector.payload['urls'])
        temp_file = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
        with open(temp_file.name, 'wb') as f:
            f.write(response.data)

        audio, sr = librosa.load(temp_file.name)
        st.audio(audio, sample_rate=sr)

    results = client.search(
        collection_name=collection, query_vector=song_vector.vector, limit=10
    )

    if results:
        for result in results:
            st.header(f"Genre: {result.payload['genre']}")
            st.markdown(f"### Artist: {result.payload['artist']}")
            st.markdown(f"#### Song name: {result.payload['name']}")
            try:
                st.audio(result.payload["urls"])
            except:
                response = http.request('GET', result.payload["urls"])
                temp_file = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
                with open(temp_file.name, 'wb') as f:
                    f.write(response.data)

                audio, sr = librosa.load(temp_file.name)
                st.audio(audio, sample_rate=sr)

elif options == 'Your Music':
    your_song = st.file_uploader(label="📀 Music file 🎸",)

    if your_song:

        audio, sr = librosa.load(your_song)
        st.audio(audio, sample_rate=sr)

        genres = classifier(a_song)

        if genres:
            st.markdown("## Best Prediction")
            col1, col2 = st.columns(2, gap="small")
            col1.subheader(genres[0]['label'])
            col2.metric(label="Score", value=f"{genres[0]['score']*100:.2f}%")

            st.markdown("### Other Predictions")
            col3, col4 = st.columns(2, gap="small")
            for idx, genre in enumerate(genres[1:]):
                if idx % 2 == 0:
                    col3.metric(label=genre['label'], value=f"{genre['score']*100:.2f}%")
                else:
                    col4.metric(label=genre['label'], value=f"{genre['score']*100:.2f}%")

        features = classifier.feature_extractor(
            a_song, sampling_rate=16_000, return_tensors="pt", padding=True, 
            return_attention_mask=True, max_length=16_000, truncation=True
        )

        with torch.no_grad():
            vectr = classifier.model(**features, output_hidden_states=True).hidden_states[-1].mean(dim=1)[0]


        results = client.search(
            collection_name=collection,
            query_vector=vectr.tolist(),
            limit=10
        )

        if results:
            st.markdown("## Semantic Search Based on Your Song")
            for result in results:
                st.header(f"Genre: {result.payload['genre']}")
                st.markdown(f"### Artist: {result.payload['artist']}")
                st.markdown(f"#### Song name: {result.payload['name']}")
                try:
                    st.audio(result.payload["urls"])
                except:
                    response = http.request('GET', result.payload["urls"])
                    temp_file = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
                    with open(temp_file.name, 'wb') as f:
                        f.write(response.data)

                    audio, sr = librosa.load(temp_file.name)
                    st.audio(audio, sample_rate=sr)