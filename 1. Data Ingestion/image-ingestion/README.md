# Satellite Data Ingestion with IBM Cloud Code Engine

satellite-ingestion provides an end-to-end serverless solution for processing and ingesting satellite data using [IBM Cloud Code Engine](https://cloud.ibm.com/docs/codeengine).


## Target audience

Satellite domain users who want to leverage this repo as a template to process their own satellite data -      
 If you are only interested in processing and ingesting your satellite data and have no intention to learn the underlying technologies (e.g. Code Engine), this repo can be used as a template that you could easily make only minor modifications to make it fit your own data, and it hides all the technical details so you don't need to learn Code Engine and just let it power your data ingestion under the hood.
 
 
## Main Features

-   **Easy to deploy**. Once [Code Engine](https://cloud.ibm.com/docs/codeengine) is properly setup, all you need to do is to use this project as a template and make minor modifications to fit your own data and use case.
-   **Easy to config**. All configurable parameters are configured in the outermost `run.sh` which underlying pushes these parameters to either [ConfigMap](https://kubernetes.io/docs/tasks/configure-pod-container/configure-pod-configmap) or [Secrets](https://kubernetes.io/docs/concepts/configuration/secret/) in the Kubernetes env. Once you are done with the one-time modification on the docker image and yaml file, all you need to do is to change the params in `run.sh` whenever you have new batches of data to process.
-   **Reliable**. With Code Engine, it is guaranteed that unfinished tasks due to dead pod will be reprocessed by a new pod.


## Repository Structure

 `modis` is the core image ingestion application which ingest the data. It uses [Modis data](https://modis.gsfc.nasa.gov/data/) as an example to process.


`buildvrt` is an add-on application that adds an enhancement (cloud optimization) to the raster output of `modis` application. If you will be leveraging raster output stored on Cloud Object Storage, you need to run this application as well.


## Prerequisites

The only requirement is to have [Code Engine](https://cloud.ibm.com/docs/codeengine) properly setup.


## Implementation

 1. **Prepare Docker Image**  
 `image-ingestion/image_ingestion.py` and `image-ingestion/Dockerfile` defines the docker image that contains the functionality of image processing. Use the existing one as template and modify it to suit your use case.
 Once you finish the modification, publish your docker image to docker hub:
```zsh
docker login
cd image-ingestion
docker build -t <user_name>/<image_name>:<image_tag> .
docker push <user_name>/<image_name>:<image_tag>
```
2. **Modify Configs**  
 - `run.sh` contains all the configs you need to modify, change the values correspondingly.
 - `image-ingestion.yaml` contains the job definition. The only required modification is the image name, where you should replace the value with your <image_name>:<image_tag> in the previous step.
 - for advanced users, you can also modify other things in both `run.sh` and `image-ingestion.yaml`. One example is to add more environment variables. This requires some basic knowledge of Kubernetes  [ConfigMap](https://kubernetes.io/docs/tasks/configure-pod-container/configure-pod-configmap) and [Secrets](https://kubernetes.io/docs/concepts/configuration/secret/).
 - You might also have to modify `image-ingestion.py` if your data is in different satellite format. The line you might want to change is `hdf_to_tif()` where you need to make modifications based on your input data format, e.g. Landsat data usually come in geotiff format so you can skip this hdf_to_tif step, while Sentinel data usually come in .SAFE format so you might want to replace hdf_to_tif with safe_to_tif. 

3. **Run It!**  
Simply run `run.sh`, that's it.

4. **[Optional] Check Running Status**  
You might want to check the status of your job. Some useful commands include:
`kubectl get pods`: check the current running pods.
`kubectl logs <pod name>`: check the logs of a particular pod.
`kubectl logs -l <label_name>=<label_value>`: check the full logs of your job. The <label_name> and <label_value> are the ones defined as *metadata.labels* in `image-ingestion.yaml`. E.g. `kubectl logs -l product=modis` for the modis application.

