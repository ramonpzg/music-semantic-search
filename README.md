# Semantic Search for Songs App


This project showcases the power of Vector Databases like Qdrant for Semantic Search and Audio 
data. If you'd like to follow along a create your own app based on this one but for your different 
playlists, please read along.

If you have never used vector databases, check out the Getting Started section of Qdrant here. If 
you want to follow a more detailed tutorial on vector databases and audio data, check out this guide 
in the Qdrant Documentation and this video on YouTube.

## Table of Contents

1. Dependencies
2. Data
    - Payload
    - Songs
2. Embeddings
3. Qdrant
4. Building an App


## 1. Data

The data can be found in Kaggle here. It contains 12GB of data, songs from all sorts of genres, 
and additional metadata that will become the payload of our vectors.

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

