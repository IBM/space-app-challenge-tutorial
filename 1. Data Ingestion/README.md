# Satellite Data Preprocessing and Ingestion

## Background
Satellite data are provided in different formats by different providers. Most of these formats are either highly compressed or provider-specific which cannot be easily used (render, query and etc.) directly. It is essential to have a unified pipeline that can take various of data and convert into the same highly efficient format for usage.

## Steps

After raw satellite data is landed in Cloud Object Storage, each image will go through two parallel pre-processing paths:
1. Raster path: satellite data get converted into Cloud Optimized GeoTiff data (COG) and stored in Cloud Object Storage. The COG output, which is optimized on Cloud Object Storage, can be used for fast raster data query.
2. Vector path: satellite data get converted into XYZ vector data (e.g. latitude, longitude, value) and stored as parquet format in Cloud Object Storage. The vector output, which is essentially a dataframe format, is analytical-ready and can be used with common SQL/ML/AI tools.

## Prerequisites and Implementations
Check [image-ingestion folder](image-ingestion) for more details.
