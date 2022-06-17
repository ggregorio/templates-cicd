import os
import boto3

# from botocore.client import Config

AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')
AWS_BUCKET_S3 = os.environ.get('AWS_BUCKET_S3')
AWS_REGION = os.environ.get('AWS_REGION')

print(AWS_ACCESS_KEY_ID)
print(AWS_SECRET_ACCESS_KEY)
print(AWS_BUCKET_S3)
print(AWS_REGION)


def create_session():
    # Creating Session With Boto3.
    session = boto3.Session(
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY
    )
    return session


def get_resource(resource_type, endpoint_url_bucket):
    session = create_session()
    s3_resource = session.resource(
        resource_type,
        endpoint_url=endpoint_url_bucket,
        region_name=AWS_REGION,
        verify=False
    )
    return s3_resource


def get_bucket(resource_type, endpoint_url_bucket):
    s3_resource = get_resource(resource_type, endpoint_url_bucket)
    s3_resurce_bucket = s3_resource.Bucket(AWS_BUCKET_S3)
    return s3_resurce_bucket


def list_objects_from_bucket(resource_type, endpoint_url_bucket, bucket_prefix):
    s3_resurce_bucket = get_bucket(resource_type, endpoint_url_bucket)
    print(s3_resurce_bucket)
    for objects in s3_resurce_bucket.objects.filter(Prefix=bucket_prefix):
        print(objects.key)


def updaload_file_to_bucket():
    uftb_resource_s3_type = "s3"
    uftb_endpoint_url_bucket_s3 = 'https://bucket.vpce-0f87e27e4855c7bd5-a7qfhx1t.s3.us-east-1.vpce.amazonaws.com'

    # uftb_bucket_s3_dir = "data/in/fluentbit/test/"
    # file_name = "DEVOPS_REPOSITORIOS_20220111.txt"

    # file_target = "{}{}".format(uftb_bucket_s3_dir, file_name)
    # path = "C:\Users\A309469\workspace\devops-reporting\get-repositories\DEVOPS_REPOSITORIOS_20220111.txt"

    uftb_dir = os.getcwd()
    print(uftb_dir)

    filePath = __file__
    print("This script file path is ", filePath)

    get_bucket(uftb_resource_s3_type, uftb_endpoint_url_bucket_s3)
    # result = s3_resurce_bucket.upload_file(Filename=path, Key=file_target)

    # print(result)


resource_s3_type = "s3"
endpoint_url_bucket_s3 = 'https://bucket.vpce-0f87e27e4855c7bd5-a7qfhx1t.s3.us-east-1.vpce.amazonaws.com'
bucket_s3_dir = "data/in/fluentbit/test/"
list_objects_from_bucket(resource_s3_type, endpoint_url_bucket_s3, bucket_s3_dir)

# for bucket in s3_connection.buckets.all():
# print(bucket.name)
# s3_connection.Bucket(AWS_BUCKET_S3).upload_file(Filename=output_file_name, Key='data/in/{}'.format(output_file_name))


updaload_file_to_bucket()
list_objects_from_bucket(resource_s3_type, endpoint_url_bucket_s3, bucket_s3_dir)
