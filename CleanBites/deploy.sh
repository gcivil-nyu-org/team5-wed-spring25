#!/bin/bash

# Define variables
AWS_REGION="us-west-2"
ECR_REPO="730335518224.dkr.ecr.us-west-2.amazonaws.com/cleanbites"
EB_ENV="CleanBites-amznlnx-docker-stable-env"

echo "🚀 Building Docker image..."
docker build --no-cache -t cleanbites .

echo "🔑 Authenticating AWS ECR..."
aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $ECR_REPO

echo "🏷️ Tagging image..."
docker tag cleanbites:latest $ECR_REPO:latest

echo "📤 Pushing image to AWS ECR..."
docker push $ECR_REPO:latest

echo "🔗 Connecting to Elastic Beanstalk instance..."
powershell.exe -Command "eb ssh $EB_ENV 'sudo docker rm -f $(sudo docker ps -q); sudo docker system prune -a -f; exit'"

echo "🚀 Deploying to Elastic Beanstalk..."
powershell.exe -Command "eb deploy $EB_ENV"

echo "✅ Deployment completed!"
