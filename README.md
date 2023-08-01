# Semantic Search for Songs App

![img](images/music_search_app.gif)

This project showcases the power of Vector Databases like Qdrant for Semantic Search and Audio 
data. If you'd like to follow along a create your own app based on this one but for your own 
playlists, please read along.

If you have never used vector databases, you should check out the 
[What is Qdrant](https://qdrant.tech/documentation/overview/) and the 
[Quick Start](https://qdrant.tech/documentation/quick-start/) sections of Qdrant's documentation, 
they will get you up to speed in a short amount of time. If you want to follow a more detailed 
tutorial on vector databases and audio data, check out 
[this notebook](https://githubtocolab.com/qdrant/examples/blob/master/qdrant_101_audio_data/03_qdrant_101_audio.ipynb) 
and this [video on YouTube](https://www.youtube.com/watch?v=id5ql-Abq4Y&t=190s&ab_channel=Qdrant).

## Table of Contents

1. Minimal Set Up (Completed :sunglasses: )
    1. Dependencies
    2. Qdrant Cloud
    3. Run App Locally
    4. Package It
    5. Deploy
2. From Scratch (In Progress)
    1. Data
        - Payload
        - Songs
    2. Embeddings
    3. Qdrant
    4. Building an App

## 1. Minimal Set Up

Clone or fork the repository.

```bash
git clone git@github.com:ramonpzg/music-semantic-search.git
```
### 1.1 Dependencies

Create a virtual environment with your favorite tool. This app was tested with python 3.10 and 3.11, but 
other versions might work well as well.

```bash
# with mamba or conda
mamba env create -n my_env python=3.11
mamba activate my_env

# or with virtualenv
python -m venv venv
source venv/bin/activate

# install packages
pip install -r requirements.txt
```

### 1.2 Qdrant Cloud

You can download the embeddings as a `.npy` file [from here](https://drive.google.com/file/d/1erBTHeTxvlz2Oz5VxcjpRlHivjPfv42h/view?usp=sharing).

Next, go to Qdrant Cloud, create an API key, and then add it to your environment as follows.

```sh
export QDRANT_API_KEY="**************************"
```

Then you are ready to add the collection to your cluster.

```python
# load_points.py
from qdrant_client import QdrantClient, models
import pandas as pd
import numpy as np
import os

collection = "music_vectors"
batch_size = 250


client = QdrantClient(
    "https://394294d5-30bb-4958-ad1a-15a3561edce5.us-east-1-0.aws.cloud.qdrant.io:6333", 
    api_key=os.environ['QDRANT_API_KEY']
)

metadata = pd.read_csv('payload.csv')
metadata['subgenres'] = metadata['subgenres'].apply(lambda x: x.tolist())
embeddings = np.load('audio_vectors.npy')
index = metadata['index'].tolist()
payload = metadata.drop(['index', 'ids'], axis=1).to_dict(orient="records")

client.recreate_collection(
    collection_name=collection,
    vectors_config=models.VectorParams(
        size=embeddings.shape[1], distance=models.Distance.COSINE
    )
)


for i in range(0, metadata.shape[0], batch_size):

    low_idx = min(i+batch_size, metadata.shape[0])

    batch_of_ids = index[i: low_idx]
    batch_of_embs = embeddings[i: low_idx]
    batch_of_payloads = payload[i: low_idx]

    client.upsert(
        collection_name=collection,
        points=models.Batch(
            ids=batch_of_ids,
            vectors=batch_of_embs.tolist(),
            payloads=batch_of_payloads
        )
    )

```

After you run the `load_points.py` file above, you are ready to test the app locally.

### 1.3 Run App Locally

```python
python main.py
```

### 1.4 Package It

Let's now package our app into a docker container. The following command will find our `Dockerfile` and 
`.dockerignore` inside our directory and build our image for us.

```bash
docker build -t music_app . 
```
Time to test the app. 

```bash
docker run -p 80:8080 -e QDRANT_API_KEY -v $(pwd)/:/app -d --restart always music_app
```

Now navigate to `https://localhost:80` in your browser and you should be able to see your app.





## 2. From Scratch

Only go through this part if you want to do the entire project from zero.

❗Please note that I am still updating this section and it is currently incomplete.

## 2.1 Data

The data can be found in [Kaggle here](https://www.kaggle.com/datasets/jorgeruizdev/ludwig-music-dataset-moods-and-subgenres). 
It contains 12GB of data, songs from all sorts of genres, and additional metadata that will become the payload of our vectors.

Once you download the data, you will need to create a bucket on AWS or in your cloud provider 
of choice as you will need an url for each of your songs once you host this application.

### Payload

The payload is available in this repo under the name `metadata.parquet` so you do not need to 
recreate it yourself. If you do want to see the logic to create it, please follow the tutorial 
here.

### Songs

Here are the steps to add the songs to an AWS bucket. This assumes you already have the `awscli` 
installed and ready to go.

```bash
# create bucket
aws s3api create-bucket --bucket your_bucket

# sync songs with bucket
aws s3 sync data/ludwig_music_data/mp3 s3://your_bucket/ludwig_music_data/mp3/
```

Now that we have the songs in our bucket, we'll need to change the permissions of the bucket 
so that our application can access them. There are different ways to go about this, we can 
completely open the bucket (straightforward), or we can create a new role and grant it permission to access 
the files in the bucket (more involved). We'll go with the former.

To grant open access to the content of an Amazon S3 bucket so that everyone anywhere 
can access the files in it, you can follow these steps using the AWS Management Console:

1. **Log in to the AWS Management Console**: Go to https://aws.amazon.com/ and sign 
in with your AWS credentials.

2. **Navigate to Amazon S3**: Once logged in, search for "S3" in the AWS services 
search bar, or you can find it under the "Storage" section in the AWS Management Console.

3. **Select your bucket**: Click on the name of the S3 bucket you want to make public.

4. **Edit Bucket Policy**: In the S3 bucket dashboard, click on the "Permissions" tab, 
and then click on "Bucket Policy."

5. **Create or Update the Bucket Policy**: In the Bucket Policy editor, you'll 
need to add a policy that grants public access to all objects in the bucket. The 
policy should look something like this:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "PublicReadGetObject",
            "Effect": "Allow",
            "Principal": "*",
            "Action": "s3:GetObject",
            "Resource": "arn:aws:s3:::your-bucket-name/*"
        }
    ]
}
```

Replace "your-bucket-name" with the actual name of your S3 bucket.

6. **Save the Bucket Policy**: After pasting the policy, click on the "Save" button 
to apply the changes.

7. **Update ACLs (Access Control List)**: In some cases, you might also need to 
update the Access Control List (ACL) to ensure public read access. Go to the 
"Permissions" tab, click on "Access Control List," and set the "Everyone (public 
access)" permissions to "Read object" for "List objects."

That's it! Your S3 bucket should now be configured to allow public access to all files 
in it. Keep in mind that making an S3 bucket public means anyone with the bucket name 
can access its contents. Be cautious when making sensitive data public and always follow 
best practices for securing your resources.

Lastly, we'll need to get the urls for each song. We'll do so in Python with the `boto3` 
library.

```python
import pandas as pd
import boto3

s3 = boto3.client('s3')
objects = s3.list_objects_v2(Bucket='datalakerpg', Prefix='ludwig_music_data/')

def get_s3_objects(bucket_name, prefix):
    paginator = s3.get_paginator('list_objects_v2')
    page_iterator = paginator.paginate(Bucket=bucket_name, Prefix=prefix)
    all_urls = []
    all_objects = []
    for page in page_iterator:
        if 'Contents' in page:
            all_objects.extend(page['Contents'])
            for obj in page['Contents']:
                # Construct the object URL
                if obj['Key'].endswith(".mp3"):
                    object_url = f"https://{bucket_name}.s3.ap-southeast-2.amazonaws.com/{obj['Key']}"
                    all_urls.append(object_url)
    return all_urls

# Replace 'your-bucket-name' with the actual bucket name
all_urls = get_s3_objects('your_bucket', 'ludwig_music_data/mp3/')

# Create a dataframe with the ids and song urls 
ids = [i.split('/')[-1].replace(".mp3", '') for i in all_urls]
music_paths = pd.DataFrame(zip(ids, all_urls), columns=["ids", 'urls'])

# combine urls with metadata dataframe
metadata = (metadata.merge(right=music_paths, how="left", left_on='ids', right_on='ids')
                    .drop("index_y", axis=1)
                    .rename({"index_x": "index"}, axis=1))

# save your new payload
metadata.to_parquet("metadata.parquet")
```