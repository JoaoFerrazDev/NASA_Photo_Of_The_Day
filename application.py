from flask import Flask, render_template, request
import requests
import os
import boto3
import botocore
import urllib.parse
import re

app = Flask(__name__)

# AWS S3 configuration
S3_BUCKET_NAME = 'nasa-photo-of-the-day'
S3_DESTINATION_FOLDER = 'photos/'


# Route to handle the form submission
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        start_date = request.form.get('start_date')
        end_date = request.form.get('end_date')
        num_of_photos = request.form.get('num_of_photos')

        # Validate and process the form inputs
        if start_date and end_date:
            # Request photos for a range of dates
            apod_images = get_apod_images_range(start_date, end_date)
        elif num_of_photos:
            # Request a specific number of photos
            apod_images = get_apod_images_count(num_of_photos)
        else:
            return 'Invalid input!'

        # Save the images to AWS S3
        save_images_to_s3(apod_images)

        return render_template('index.html', apod_images=apod_images)

    return render_template('index.html')


# Function to retrieve APOD images for a range of dates
def get_apod_images_range(start_date, end_date):
    url = f'https://api.nasa.gov/planetary/apod?start_date={start_date}&end_date={end_date}&api_key=VNZSb5QdAhN1P3O36xZdKTS8LASnnHjPIcWMXkoX'
    response = requests.get(url)
    apod_images = response.json()
    return apod_images


# Function to retrieve a specific number of APOD images
def get_apod_images_count(num_of_photos):
    url = f'https://api.nasa.gov/planetary/apod?count={num_of_photos}&api_key=VNZSb5QdAhN1P3O36xZdKTS8LASnnHjPIcWMXkoX'
    response = requests.get(url)
    apod_images = response.json()
    return apod_images


# Function to sanitize filename
def sanitize_filename(filename):
    # Replace invalid characters with underscores
    return re.sub(r'[\/:*?"<>|]', '_', filename)


# Function to save images to AWS S3
def save_images_to_s3(apod_images):
    s3 = boto3.client('s3', region_name="eu-west-1")

    print(apod_images)

    for image in apod_images:
        image_url = image['url']
        image_title = image['title']
        image_filename = sanitize_filename(image_title) + '.jpg'
        response = requests.get(image_url, verify=True)

        # Save the image locally
        with open(image_filename, 'wb') as f:
            f.write(response.content)

        # Upload the image to S3
        s3_key = S3_DESTINATION_FOLDER + image_filename
        s3.upload_file(image_filename, S3_BUCKET_NAME, s3_key)

        # Remove the local image file
        os.remove(image_filename)


if __name__ == '__main__':
    app.run()
