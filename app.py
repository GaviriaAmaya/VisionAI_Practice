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

    # Result function

    # Create a client for data response
    ds_client = datastore.Client()

    # Take the date time
    date = datetime.now()

    # Define Datastore entity key
    kind = 'Labels'
    name = blob.name
    label_key = ds_client.key(kind, name)

    # New entity based on data. ASAP will contain name, mail.
    # This is a test
    entity = datastore.Entity(label_key)
    entity['blob_name'] = name
    entity['image_public_url'] = blob.public_url
    entity['date'] = date
    # entity['result'] = result

    # Save the entity on Datastore
    ds_client.put(entity)

    return redirect('/')

@app.errorhandler(500)
def server_error(e):
    logging.exception('An error occurred during a request.')
    return """
    An internal error occurred: <pre>{}</pre>
    See logs for full stacktrace.
    """.format(e), 500

if __name__ == "__main__":
    app.run(host='127.0.0.1', port=8080, debug=True)