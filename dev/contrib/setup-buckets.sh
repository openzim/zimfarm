#!/bin/bash

MINIO_ALIAS="dev_minio"
MINIO_URL="http://minio:9000"
MINIO_USER="minio_key"
MINIO_PASSWORD="minio_secret"
BUCKETS=("zimfarm-artifacts" "zimfarm-logs" "zimfarm-zimchecks" "zimfarm-zims")

# Wait for MinIO
echo "Waiting for MinIO to be ready..."
for i in $(seq 1 30); do
    # Set up MinIO alias if it's ready
    /usr/bin/mc alias set $MINIO_ALIAS $MINIO_URL $MINIO_USER $MINIO_PASSWORD && echo "MinIO is ready!" && break
    sleep 2
    [ "$i" -eq 30 ] && { echo "ERROR: MinIO timeout"; exit 1; }
done

# Setup buckets
for bucket in "${BUCKETS[@]}"; do
    echo "Setting up bucket: $bucket"
    /usr/bin/mc mb "$MINIO_ALIAS/$bucket" --ignore-existing # Create bucket if it doesn't exist
    /usr/bin/mc anonymous set public "$MINIO_ALIAS/$bucket" # Set bucket to public
done
echo "MinIO setup complete"
