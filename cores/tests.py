import boto3
import unittest
from moto import mock_s3

from django.conf import settings

from .utils import validate_upload_file, delete_existing_image, handle_upload_file


def func_to_test(bucket_name, key, content):
    s3 = boto3.resource('s3')
    object = s3.Object(bucket_name, key)
    object.put(Body=content)

class MyTest(unittest.TestCase):
    mock_s3 = mock_s3()
    bucket_name = 'moto-test-bucket'
    def setUp(self):
        self.mock_s3.start()

        s3 = boto3.resource('s3')
        bucket = s3.Bucket(self.bucket_name)
        bucket.create(CreateBucketConfiguration={'LocationConstraint': "ap-northeast-2"},)

    def tearDown(self):
        self.mock_s3.stop()

    def test(self):
        content = b"abc"
        key = '/moto-test'

        func_to_test(self.bucket_name, key, content)

        s3 = boto3.resource('s3')
        object = s3.Object(self.bucket_name, key)
        actual = object.get()['Body'].read()
        self.assertEqual(actual, content)