# Doc reference: https://docs.digitalocean.com/products/spaces/resources/s3-sdk-examples/
import boto3

from decouple import config

session = boto3.session.Session()

spaces_client = session.client('s3',

                               region_name='sgp1',

                               endpoint_url='https://sgp1.digitaloceanspaces.com',

                               aws_access_key_id=config('SPACES_ACCESS'),

                               aws_secret_access_key=config('SPACES_SECRET'))


def get_upload_presigned_url(file_name):
    url = spaces_client.generate_presigned_url(ClientMethod='put_object',

                                               Params={

                                                   'Bucket': 'pointapp',

                                                   'Key': file_name,

                                                   'ContentType': "image/jpeg",
                                                   'ACL': 'public-read'

                                               },

                                               ExpiresIn=600)

    return url


def get_download_presigned_url(file_name):
    url = spaces_client.generate_presigned_url(ClientMethod='get_object',

                                               Params={'Bucket': 'pointapp',
                                                       'Key': file_name,

                                                       },

                                               ExpiresIn=600)

    return url


def list_presigned_url(file_path):
    response = spaces_client.list_objects(Bucket='pointapp', Prefix=file_path)
    for obj in response['Contents']:
        print(obj['Key'])
