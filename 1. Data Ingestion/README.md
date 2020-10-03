# Satellite Data Preprocessing and Ingestion

## Background
Satellite data are provided in different formats by different providers. Most of these formats are either highly compressed or provider-specific which cannot be easily used (render, query and etc.) directly. It is essential to have a unified pipeline that can take various of data and convert into the same highly efficient format for usage.

## Steps

After raw satellite data is landed in Cloud Object Storage, each image will go through two parallel pre-processing paths:
1. Raster path: satellite data get converted into Cloud Optimized GeoTiff data (COG) and stored in Cloud Object Storage. The COG output, which is optimized on Cloud Object Storage, can be used for fast raster data query.
2. Vector path: satellite data get converted into XYZ vector data (e.g. latitude, longitude, value) and stored as parquet format in Cloud Object Storage. The vector output, which is essentially a dataframe format, is analytical-ready and can be used with common SQL/ML/AI tools.

## Prerequisites and Implementations
Check [image-ingestion folder](image-ingestion) for more details.

## Notes:
Please note that, this part can be the most challenging part to follow during the whole tutorial session. You will need to sign up couple cloud services, as well as acquiring some basic knowledge about things like docker images and kubernetes yaml files. This is, unfortunately, unavoidable as we want to provide you the serverless computation power to do your data processing as the volume of satellite data can be too large to be processed on any laptop. If you find yourself hard to follow, please don't hesitate to reach out.  Also, if you are starting with a relatively small amount of files and is ok with processing the data in your own env to avoid learning this part, you can easily do so by leveraging the image-ingestion.py file as that contains the full functionality to do the data ingestion (everything else is just wrapping that function into a docker image and further into a serverless cluster to do the computation). 
