#!/bin/zsh

# COS credentials (set your credentials here or use env variable)
endpoint_url=$ENDPOINT_URL
access_key_id=$ACCESS_KEY_ID
secret_access_key=$SECRET_ACCESS_KEY

# COS bucket and prefix
product=MOD11A1.006

bucket=modis
prefix=processed_images/product=$product
subprefix_depth=2 # depth from given prefix to desired subprefix, e.g. with processed_images/product=xxx/layer=xxx/date=xxx/, prefix=processed_images/product=xxx and subprefix_depth=2

# Product specifics
resolution=0.01

# Create kube secrets
echo $(date '+%m/%d/%Y %H:%M:%S') "Creating Secrets..."
until
kubectl create secret generic satellite-secrets \
--from-literal=endpoint_url=$endpoint_url \
--from-literal=access_key_id=$access_key_id \
--from-literal=secret_access_key=$secret_access_key \
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
--from-literal=bucket=$bucket \
--from-literal=prefix=$prefix \
--from-literal=subprefix_depth=$subprefix_depth \
--from-literal=resolution=$resolution \
-o yaml \
--dry-run \
| kubectl apply -f -
do
	echo $(date '+%m/%d/%Y %H:%M:%S') "Failed on creating configs, retrying..."
	sleep 60
done

# Submit job
echo $(date '+%m/%d/%Y %H:%M:%S') "Creating JobRun..."
until kubectl create -f image-ingestion.yaml
do
	echo $(date '+%m/%d/%Y %H:%M:%S') "Failed on creating job, retrying..."
	sleep 60
done
echo $(date '+%m/%d/%Y %H:%M:%S') "Waiting JobRun to Finish..."
until kubectl wait --for=condition=complete --timeout=-1s jobrun image-ingestion
do
	echo $(date '+%m/%d/%Y %H:%M:%S') "Failed on waiting job, retrying..."
	sleep 60
done
echo $(date '+%m/%d/%Y %H:%M:%S') "Deleting JobRun..."
until kubectl delete jobrun image-ingestion
do
	echo $(date '+%m/%d/%Y %H:%M:%S') "Failed on deleting job, retrying..."
	sleep 60
done
