#!/bin/bash
set -e

# Configuration
VM_NAME="worker-redis-vm"
ZONE="us-east1-b"
MACHINE_TYPE="e2-small"
IMAGE_FAMILY="ubuntu-2204-lts"
IMAGE_PROJECT="ubuntu-os-cloud"
TAGS="redis-server"

# Load env vars
if [ -f .env.production ]; then
    export $(grep -v '^#' .env.production | xargs)
else
    echo "Error: .env.production file not found."
    exit 1
fi

echo "--- Deploying Worker VM: $VM_NAME ---"

# 1. Check if VM exists
if gcloud compute instances describe $VM_NAME --zone=$ZONE > /dev/null 2>&1; then
    echo "VM $VM_NAME already exists."
else
    echo "Creating VM $VM_NAME..."
    gcloud compute instances create $VM_NAME \
        --quiet \
        --zone=$ZONE \
        --machine-type=$MACHINE_TYPE \
        --image-family=$IMAGE_FAMILY \
        --image-project=$IMAGE_PROJECT \
        --tags=$TAGS \
        --boot-disk-size=20GB \
        --metadata=startup-script='#! /bin/bash
        apt-get update
        apt-get install -y docker.io docker-compose
        '
    echo "Waiting for VM to initialize..."
    sleep 60
fi

# 2. Configure Firewall
echo "Configuring Firewall..."
if ! gcloud compute firewall-rules describe allow-redis > /dev/null 2>&1; then
    gcloud compute firewall-rules create allow-redis \
        --quiet \
        --allow tcp:6379 \
        --target-tags=$TAGS \
        --description="Allow Redis access"
fi

# 3. Get VM IP
VM_IP=$(gcloud compute instances describe $VM_NAME --zone=$ZONE --format='get(networkInterfaces[0].accessConfigs[0].natIP)')
echo "VM Public IP: $VM_IP"

# 4. Update .env.production with real IP for local use/Cloud Run
# Note: This updates the local file, you might want to be careful if running multiple times
sed -i '' "s/worker-redis-vm/$VM_IP/g" .env.production

# 5. Package and Copy files to VM
echo "Packaging source code..."
git archive --format=tar.gz -o worker-deploy.tar.gz HEAD

echo "Copying configuration and code to VM..."
gcloud compute scp --quiet --zone=$ZONE .env.production worker-deploy.tar.gz infra/docker-compose.worker.yml $VM_NAME:~/

# 6. Deploy on VM
echo "Deploying Docker stack on VM..."
gcloud compute ssh $VM_NAME --quiet --zone=$ZONE --command="
    # Clean up previous deployment
    rm -rf app
    mkdir -p app
    
    # Extract code
    tar -xzf worker-deploy.tar.gz -C app
    mv docker-compose.worker.yml app/docker-compose.yml
    mv .env.production app/.env
    
    cd app
    
    # Deploy
    sudo docker-compose down
    sudo docker-compose up -d --build
"

# Cleanup local tarball
rm worker-deploy.tar.gz

echo "--- Worker Deployment Complete ---"
echo "Redis is available at: redis://:$REDIS_PASSWORD@$VM_IP:6379"
echo "Don't forget to update your Cloud Run services with this REDIS_URL!"
