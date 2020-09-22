import os
import numpy as np
import datetime
import ibm_boto3
from pyrip.cog import build_vrt

### Configurations ###

# COS credentials
access_key_id = os.environ['ACCESS_KEY_ID']
secret_access_key = os.environ['SECRET_ACCESS_KEY']
endpoint_url = os.environ['ENDPOINT_URL']
endpoint = endpoint_url.replace('https://', '')

# COS bucket and prefix
bucket = os.environ['BUCKET']
prefix = os.environ['PREFIX']
subprefix_depth = int(os.environ['SUBPREFIX_DEPTH'])

# Product specifics
resolution = float(os.environ['RESOLUTION'])


### Functions ###

# Get all urls under the bucket and prefix
def get_all_keys(bucket, prefix='', suffix=''):
    kwargs = {'Bucket': bucket, 'Prefix': prefix}
    while True:
        resp = cos.list_objects_v2(**kwargs)
        try:
            contents = resp['Contents']
        except KeyError:
            return
        for obj in contents:
            key = obj['Key']
            if key.endswith(suffix):
                yield key
        try:
            kwargs['ContinuationToken'] = resp['NextContinuationToken']
        except KeyError:
            break


# Get sub-prefixes under the given bucket and prefix
def get_subprefixes(bucket, prefix=''):
    kwargs = {'Bucket': bucket, 'Prefix': prefix, 'Delimiter': '/'}
    while True:
        resp = cos.list_objects_v2(**kwargs)
        for common_prefix in resp.get('CommonPrefixes', []):
            yield common_prefix['Prefix']
        try:
            kwargs['ContinuationToken'] = resp['NextContinuationToken']
        except KeyError:
            break


# Get all sub-prefixes at certain depth under the given bucket and prefix
def get_subprefixes_at_depth(bucket, prefix='', depth=1):
    prefix = os.path.join(prefix, '') # add trailing slash if not there
    prefixes = [prefix]
    for _ in range(depth):
        prefixes = [subprefix for prefix in prefixes for subprefix in get_subprefixes(bucket, prefix)]
    return prefixes


# Main func to process images
def process(subprefix):
    vrt_file = os.path.join('/vsis3', bucket, subprefix, 'index.vrt')
    cog_files = [os.path.join('/vsis3', bucket, key) for key in get_all_keys(bucket, subprefix, '.tif')]
    build_vrt(vrt_file, cog_files, resolution=resolution, access_key_id=access_key_id, secret_access_key=secret_access_key, endpoint=endpoint)


### Main Process ###

# Create cos client
cos = ibm_boto3.client('s3',
    aws_access_key_id=access_key_id,
    aws_secret_access_key=secret_access_key,
    endpoint_url=endpoint_url
)


# Process image batch based on JOB_INDEX
job_index = int(os.environ['JOB_INDEX'])
array_size = int(os.environ['ARRAY_SIZE'])
all_subprefixes = get_subprefixes_at_depth(bucket, prefix, subprefix_depth)
subprefixes = np.array_split(all_subprefixes, array_size)[job_index]

print('To be processed:', subprefixes)
for subprefix in subprefixes:
    print(datetime.datetime.now(), "Working on ", subprefix)
    process(subprefix)
    print(datetime.datetime.now(), "Finished on ", subprefix)


