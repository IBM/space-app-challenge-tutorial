# GDAL layers
FROM continuumio/miniconda3
RUN conda install gdal=2.3.3

# other dependencies layers
RUN pip install ibm-cos-sdk pyarrow

# pyrip layers
RUN pip install pyrip==1.4.2

# Application Layer
COPY image_ingestion.py .
ENTRYPOINT ["python", "-u", "image_ingestion.py"]
