#!/bin/zsh

# COS credentials (set your credentials here or use env variable)
in_endpoint_url=$ENDPOINT_URL
in_api_key=$API_KEY
in_resource_crn=$RESOURCE_CRN

out_endpoint_url=$in_endpoint_url
out_api_key=$in_api_key
out_resource_crn=$in_resource_crn

# COS bucket and prefix
product=MOD11A1.006

in_bucket=modis
in_prefix=data/product=$product
in_suffix=.hdf

out_bucket=$in_bucket
out_image_prefix=processed_images/product=$product
out_xyz_prefix=processed_xyz/product=$product

# Product specifics
## comma separated layer substrings, e.g. layer_selector=NDVI,EVI will only select layers with name contains "DNVI" or "EVI"
layer_selector=LST

# Create kube secrets
echo $(date '+%m/%d/%Y %H:%M:%S') "Creating Secrets..."
until
kubectl create secret generic satellite-secrets \
--from-literal=in_endpoint_url=$in_endpoint_url \
--from-literal=in_api_key=$in_api_key \
--from-literal=in_resource_crn=$in_resource_crn \
--from-literal=out_endpoint_url=$out_endpoint_url \
--from-literal=out_api_key=$out_api_key \
--from-literal=out_resource_crn=$out_resource_crn \
-o yaml \
--dry-run \
| kubectl apply -f -
do
	echo $(date '+%m/%d/%Y %H:%M:%S') "Failed on creating secrets, retrying..."
	sleep 60
done

# Create kube configmaps
echo $(date '+%m/%d/%Y %H:%M:%S') "Creating Configs..."
until
kubectl create configmap satellite-configs \
--from-literal=in_bucket=$in_bucket \
--from-literal=in_prefix=$in_prefix \
--from-literal=in_suffix=$in_suffix \
--from-literal=out_bucket=$out_bucket \
--from-literal=out_image_prefix=$out_image_prefix \
--from-literal=out_xyz_prefix=$out_xyz_prefix \
--from-literal=layer_selector=$layer_selector \
-o yaml \
--dry-run \
| kubectl apply -f -
do
	echo $(date '+%m/%d/%Y %H:%M:%S') "Failed on creating configs, retrying..."
	sleep 60
done

# Submit job
start_index=0  # which index to start/resume
concurrent_jobs=64  # number of concurrent running pods, i.e. min(256/memory, 64/cpu)
############################################################################################################
## use the value of ARRAY_SIZE in yaml file, set to a number so that each pod will finish within 2 hours. ##
## For example, if we have n files to process in total, then n files will be splitted into total_jobs     ##
## chunks each with n/total_jobs files. So each pod will process n/total_jobs files, tune this number to  ##
## make sure each pod can finish n/total_jobs files in 2 hours.                                           ##
############################################################################################################
total_jobs=64
end_index=$((total_jobs - 1))  # final index, i.e. total_jobs - 1

for i in $(seq $start_index $concurrent_jobs $end_index)
do
	start=$i
	end=$((i + concurrent_jobs - 1))
	end=$((end <= end_index ? end : end_index ))
	echo $(date '+%m/%d/%Y %H:%M:%S') "Creating JobRun $start-$end..."
	until cat image-ingestion.yaml | sed "s/\$JOB_INDICES/$start-$end/" | kubectl apply -f -
	do
		echo $(date '+%m/%d/%Y %H:%M:%S') "Failed on creating job, retrying..."
		sleep 60
	done
	echo $(date '+%m/%d/%Y %H:%M:%S') "Waiting JobRun $start-$end to Finish..."
	until kubectl wait --for=condition=complete --timeout=-1s jobrun image-ingestion
	do
		echo $(date '+%m/%d/%Y %H:%M:%S') "Failed on waiting job, retrying..."
		sleep 60
	done
	echo $(date '+%m/%d/%Y %H:%M:%S') "Deleting JobRun $start-$end..."
	until kubectl delete jobrun image-ingestion
	do
		echo $(date '+%m/%d/%Y %H:%M:%S') "Failed on deleting job, retrying..."
		sleep 60
	done
	sleep 60
done
# kubectl create -f image-ingestion.yaml
