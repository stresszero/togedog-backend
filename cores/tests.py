import boto3
import unittest
from enum import Enum
from moto import mock_s3

from django.test import TestCase
from .models import EnumField

# from django.conf import settings

# from .utils import validate_upload_file, delete_existing_image, handle_upload_file


def func_to_test(bucket_name, key, content):
    s3 = boto3.resource("s3")
    test_object = s3.Object(bucket_name, key)
    test_object.put(Body=content)


class S3ServiceTest(unittest.TestCase):
    mock_s3 = mock_s3()
    bucket_name = "moto-test-bucket"

    def setUp(self):
        self.mock_s3.start()
        self.s3_resource = boto3.resource("s3")
        bucket = self.s3_resource.Bucket(self.bucket_name)
        bucket.create(
            CreateBucketConfiguration={"LocationConstraint": "ap-northeast-2"},
        )

    def tearDown(self):
        self.mock_s3.stop()

    def test_upload(self):
        content = b"abc"
        key = "/moto-test"
        func_to_test(self.bucket_name, key, content)

        test_object = self.s3_resource.Object(self.bucket_name, key)
        actual = test_object.get()["Body"].read()
        self.assertEqual(actual, content)


class EnumFieldTest(TestCase):
    def test_enumfield_requirement(self):
        with self.assertRaises(TypeError):
            EnumField()

    def test_get_default_error(self):
        field = EnumField(enum=TestEnum, default="hello")
        with self.assertRaises(AttributeError):
            field.get_default()

    def test_check_get_default_value(self):
        field = EnumField(enum=TestEnum, default=TestEnum.UNIT)
        value = field.get_default()
        self.assertEqual(value, TestEnum.UNIT)

    def test_to_python_method(self):
        field = EnumField(enum=TestEnum, default=TestEnum.UNIT)
        value = field.to_python(value=TestEnum.TEST)
        self.assertEqual(value, TestEnum.TEST.value)

        value = field.to_python(value=TestEnum.TEST.value)
        self.assertEqual(value, TestEnum.TEST.value)

        value = field.to_python(value="Test")
        self.assertEqual(value, TestEnum.TEST.value)

    def test_validate_enum(self):
        field = EnumField(enum=TestEnum)
        with self.assertRaises(AttributeError):
            field.validate_enum(AnotherTestEnum.YOU)


class TestEnum(Enum):
    TEST = "Test"
    UNIT = "Unit"


class AnotherTestEnum(Enum):
    YOU = "YOU"
    AND = "AND"
