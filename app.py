from datetime import datetime
from flask import Flask, render_template, request, redirect
from google.cloud import datastore, storage, vision
import logging
from os import environ

# Cloud Storage. It's a NoSQL DB. Allows Object saving
CLOUD_STORAGE_BUCKET = environ.get('CLOUD_STORAGE_BUCKET')

app = Flask(__name__)

# Define main page
@app.route('/')
def landing():
    # Create a Datastore CLient for DB.
    ds_client = datastore.Client()
    # Fetch information of each uploaded photo on datastore
    query = ds_client.query(kind='Labels')
    image_entities = list(query.fetch())

    # Return Flask template with image
    return render_template('homepage.html', image_entities=image_entities)

@app.route('/upload_image', methods=['GET', 'POST'])
def upload_image():
    # Request a file
    image = request.files['file']
    
    # Create storage client
    storage_client = storage.Client()

    # Get bucket for the file that will be uploaded
    bucket = storage_client.get_bucket(CLOUD_STORAGE_BUCKET)

    # Create a blob to upload the file's content
    blob = bucket.blob(image.filename)
    blob.upload_from_string(image.read(), content_type=image.content_type)

    # Public view of blob
    blob.make_public()

    # Vision client
    v_client = vision.ImageAnnotatorClient()

    source_uri = 'gs://{}/{}'.format(CLOUD_STORAGE_BUCKET, blob.name)
    analyzed_image = vision.types.Image(
        source=vision.types.ImageSource(gcs_image_uri=source_uri))
    labels = v_client.label_detection(analyzed_image)

    