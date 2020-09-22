import os
import sys
import numpy as np
import pandas as pd
import tempfile
import datetime
import time
import warnings
import ibm_boto3
from ibm_botocore.client import Config
from pyrip.warp import reproject
from pyrip.cog import optimize, validate
from pyrip.transform import hdf_to_tif, tif_to_df

### Configurations ###

# COS credentials
in_endpoint_url = os.environ['IN_ENDPOINT_URL']
in_api_key = os.environ['IN_API_KEY']
in_resource_crn = os.environ['IN_RESOURCE_CRN']

out_endpoint_url = os.environ['OUT_ENDPOINT_URL']
out_api_key = os.environ['OUT_API_KEY']
out_resource_crn = os.environ['OUT_RESOURCE_CRN']

# COS bucket and prefix
in_bucket = os.environ['IN_BUCKET']
in_prefix = os.environ['IN_PREFIX']
in_suffix = os.environ['IN_SUFFIX']

out_bucket = os.environ['OUT_BUCKET']
out_image_prefix = os.environ['OUT_IMAGE_PREFIX']
out_xyz_prefix = os.environ['OUT_XYZ_PREFIX']

# Product specifics
layer_selector = os.environ['LAYER_SELECTOR']


### Functions ###

# Get all urls under the bucket and prefix
def get_all_urls(cos_client, bucket, prefix='', suffix=''):
    kwargs = {'Bucket': bucket, 'Prefix': prefix}
    while True:
        resp = cos_client.list_objects_v2(**kwargs)
        try:
            contents = resp['Contents']
        except KeyError:
            return
        for obj in contents:
            key = obj['Key']
            if key.endswith(suffix):
                yield os.path.join(bucket, key)
        try:
            kwargs['ContinuationToken'] = resp['NextContinuationToken']
        except KeyError:
            break


# Main func to process image
def process_image(url):
    with tempfile.TemporaryDirectory() as tmpdir:
        try:
            # Step 1. Download raw hdf to local
            step = 1
            bucket, key = url.split('/', 1)
            raw_file = os.path.join(tmpdir, os.path.basename(key))
            while True:
                try:
                    in_cos.download_file(bucket, key, raw_file)
                    break
                except:
                    warnings.warn('Raw image download failed on {}, retrying...'.format(url))
                    time.sleep(60)

            # Step 2. Convert hdf to geotiff
            step = 2
            raw_tif_files = hdf_to_tif(raw_file, match_substrs=layer_selector.split(','))

            for raw_tif_file in raw_tif_files:
                try:
                    # Step 3. Reproject image to EPSG:4326
                    step = 3
                    reprojected_tif_file = reproject(raw_tif_file)

                    # Step 4. Optimize geotiff
                    step = 4
                    optimized_tif_file = optimize(reprojected_tif_file)
                    assert validate(optimized_tif_file, quiet=True)

                    # Step 5. Retrieve image information from file name
                    step = 5
                    basename = os.path.splitext(os.path.basename(raw_tif_file))[0]
                    layer = basename.split('.')[0] + '_' + basename.split('.')[-1].replace(' ', '_')
                    date = datetime.datetime.strptime(basename.split('.')[1], 'A%Y%j').strftime('%Y%m%d')

                    # Step 6. Upload COG to COS
                    step = 6
                    while True:
                        try:
                            out_cos.upload_file(optimized_tif_file, out_bucket, '{}/layer={}/date={}/{}'.format(out_image_prefix, layer, date, os.path.basename(raw_tif_file).replace(' ', '_')))
                            break
                        except:
                            warnings.warn('Processed image upload failed on {}, retrying...'.format(file))
                            time.sleep(60)

                    # Step 7. Write pixel-level vector data to COS
                    step = 7
                    parquet_file = os.path.splitext(raw_tif_file)[0]+'.snappy.parquet'
                    tif_to_df(reprojected_tif_file).to_parquet(parquet_file, engine='pyarrow', compression='snappy', index=False)
                    while True:
                        try:
                            out_cos.upload_file(parquet_file, out_bucket, '{}/layer={}/date={}/{}'.format(out_xyz_prefix, layer, date, os.path.basename(parquet_file).replace(' ', '_')))
                            break
                        except:
                            warnings.warn('Processed xyz upload failed on {}, retrying...'.format(parquet_file))
                            time.sleep(60)

                except Exception as e:
                    print('Failed on item: ', url)
                    print('Failed on file: ', raw_tif_file)
                    print('Failed on step: ', step)
                    print('Failed on reason: ', e)
   
        except Exception as e:
            print('Failed on item: ', url)
            print('Failed on step: ', step)
            print('Failed on reason: ', e)  


### Main Process ###

# Create cos sessions and clients
in_session = ibm_boto3.session.Session(ibm_api_key_id=in_api_key, ibm_service_instance_id=in_resource_crn, ibm_auth_endpoint="https://iam.cloud.ibm.com/identity/token")
out_session = ibm_boto3.session.Session(ibm_api_key_id=out_api_key, ibm_service_instance_id=out_resource_crn, ibm_auth_endpoint="https://iam.cloud.ibm.com/identity/token")
in_cos = in_session.client('s3', endpoint_url=in_endpoint_url, config=Config(signature_version="oauth"))
out_cos = out_session.client('s3', endpoint_url=out_endpoint_url, config=Config(signature_version="oauth"))


# Process image batch based on JOB_INDEX
job_index = int(os.environ['JOB_INDEX'])
array_size = int(os.environ['ARRAY_SIZE'])
all_urls = list(get_all_urls(in_cos, in_bucket, in_prefix, in_suffix))
all_urls = [url for url in all_urls if url.split('/')[3].split('=')[1]>='20190101' and url.split('/')[3].split('=')[1]<='20191231']
urls = np.array_split(all_urls, array_size)[job_index]

print('To be processed:', urls)
for url in urls:
    print(datetime.datetime.now(), "Working on ", url)
    process_image(url)
    print(datetime.datetime.now(), "Finished on ", url)


