import boto3
import unittest
from moto import mock_s3

from django.conf import settings


s3_resource = boto3.resource(
    's3', 
    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
    endpoint_url=settings.AWS_S3_ENDPOINT_URL,
)

def func_to_test(bucket_name, key, content):
    s3 = s3_resource
    object = s3.Object(bucket_name, key)
    object.put(Body=content)

class MyTest(unittest.TestCase):
    mock_s3 = mock_s3()
    bucket_name = 'moto-test-bucket'

    def setUp(self):
        self.mock_s3.start()

        # you can use boto3.client('s3') if you prefer
        s3 = s3_resource
        bucket = s3.Bucket(self.bucket_name)
        bucket.create()

    def tearDown(self):
        self.mock_s3.stop()

    def test(self):
        content = b"abc"
        key = '/path/to/obj'

        # run the file which uploads to S3
        func_to_test(self.bucket_name, key, content)

        # check the file was uploaded as expected
        s3 = s3_resource
        object = s3.Object(self.bucket_name, key)
        actual = object.get()['Body'].read()
        self.assertEqual(actual, content)
