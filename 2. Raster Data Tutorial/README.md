# Query Raster Data

## Background
During ingestion pipeline, we converted various of satellite formats into a unified COG (Cloud Optimized GeoTiff) format. The advantage of this format is that it allows efficient data retrival from Cloud Object Storage. In the demo below, you will find that we can achieve sub-second level performance on arbitray spatiotemporal selection from 10 years global images. Asides from the performance, it is also cost-effective as underlying it will only read the corresponding byte range of the objects instead of reading the whole objects and filtering.

## Demo
Follow [this example notebook](Cloud%20Optimized%20GeoTIFF%20Usage%20Demo.ipynb) on how to query arbitrary region on arbitrary date from underlying 10 years global images.
