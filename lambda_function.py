import boto3
import botocore
import os
import sys
import uuid
from urllib.parse import unquote_plus
from PIL import Image
import PIL.Image
import re
from io import BytesIO

s3 = boto3.resource('s3')

BUCKET = os.environ.get('BUCKET','')
URL = os.environ.get('URL','')

#Array for saving the allow dimensions
ALLOWED_DIMENSIONS = []

#Process the env variable ALLOWED_DIMENSIONS finding the allow dimensions
if(os.environ.get('ALLOWED_DIMENSIONS','')):
    dimensions = os.environ.get('ALLOWED_DIMENSIONS','').split(',')
    for x in dimensions:
        ALLOWED_DIMENSIONS.append(x)

#Resize the image and save the new image size in the request directory example /300x300/
def resize_image(bucket_name,original_key, key, size):
    size_split = size.split('x')
    obj = s3.Object(bucket_name=bucket_name, key=original_key)
    obj_body = obj.get()['Body'].read()
    img = Image.open(BytesIO(obj_body))
    img = img.resize((int(size_split[0]), int(size_split[1])), PIL.Image.ANTIALIAS)
    buffer = BytesIO()
    img.convert('RGB').save(buffer, 'JPEG')
    buffer.seek(0)
    obj = s3.Object(bucket_name=bucket_name, key=key)
    obj.put(Body=buffer, ContentType='image/jpeg')
    return True

#Main function inside the lambda service
def lambda_handler(event, context):
    key = event['queryStringParameters'].get('key', None)
    search = re.search( r'((\d+)x(\d+))\/(.*)', key)
    dimension = search.group(1)
    width = search.group(2)
    height = search.group(3)
    original_key = search.group(4)

    #Send forbidden if the request include a dimension not allow
    if(len(ALLOWED_DIMENSIONS)>0 and not(dimension in ALLOWED_DIMENSIONS)):
        return{
            'statusCode': 403,
            'headers': '',
            'body':'',
            }

    resize_result = resize_image(os.environ['BUCKET'], original_key, key, dimension)
    
    #After a successful resize send the location of the image
    return {
        'statusCode': 301,
        'headers': {'location': URL+"/"+key},
        'body': '',
    }