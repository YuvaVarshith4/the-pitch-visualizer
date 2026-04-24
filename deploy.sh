#!/bin/bash

# Pitch Visualizer Deployment Script
# Usage: ./deploy.sh [docker|k8s|production]

set -e

DEPLOYMENT_TYPE=${1:-docker}
ENVIRONMENT=${2:-production}

echo "🚀 Starting Pitch Visualizer Deployment..."
echo "Deployment Type: $DEPLOYMENT_TYPE"
echo "Environment: $ENVIRONMENT"

# Function to check if required environment variables are set
check_env_vars() {
    echo "🔍 Checking environment variables..."
    
    required_vars=("GROQ_API_KEY")
    if [ "$USE_POLLINATIONS" != "true" ]; then
        required_vars+=("HF_API_TOKEN")
    fi
    
    for var in "${required_vars[@]}"; do
        if [ -z "${!var}" ]; then
            echo "❌ Error: $var is not set"
            echo "Please set it in your .env file or export it as environment variable"
            exit 1
        fi
    done
    
    echo "✅ Environment variables check passed"
}

# Function to build Docker image
build_docker() {
    echo "🐳 Building Docker image..."
    docker build -t pitch-visualizer:latest .
    echo "✅ Docker image built successfully"
}

# Function to deploy with Docker Compose
deploy_docker() {
    echo "🐳 Deploying with Docker Compose..."
    
    check_env_vars
    
    # Create .env file for docker-compose if it doesn't exist
    if [ ! -f .env ]; then
        echo "📝 Creating .env file from environment variables..."
        cat > .env << EOF
GROQ_API_KEY=${GROQ_API_KEY}
HF_API_TOKEN=${HF_API_TOKEN}
USE_POLLINATIONS=${USE_POLLINATIONS:-true}
ENCRYPTION_KEY=${ENCRYPTION_KEY:-16ByteSecretKey!}
ENCRYPTION_IV=${ENCRYPTION_IV:-16ByteInitVector}
EOF
    fi
    
    docker-compose down
    docker-compose up -d
    
    echo "✅ Docker deployment completed"
    echo "🌐 Application available at: http://localhost:8000"
}

# Function to deploy to Kubernetes
deploy_k8s() {
    echo "☸️ Deploying to Kubernetes..."
    
    check_env_vars
    
    # Build and push Docker image (modify registry as needed)
    build_docker
    docker tag pitch-visualizer:latest your-registry/pitch-visualizer:latest
    docker push your-registry/pitch-visualizer:latest
    
    # Update the image in k8s-deployment.yaml
    sed -i 's|image: pitch-visualizer:latest|image: your-registry/pitch-visualizer:latest|' k8s-deployment.yaml
    
    # Encode secrets (you should do this securely)
    echo "🔐 Encoding secrets for Kubernetes..."
    kubectl create secret generic pitch-visualizer-secrets \
        --from-literal=groq-api-key="$GROQ_API_KEY" \
        --from-literal=hf-api-token="$HF_API_TOKEN" \
        --from-literal=encryption-key="${ENCRYPTION_KEY:-16ByteSecretKey!}" \
        --from-literal=encryption-iv="${ENCRYPTION_IV:-16ByteInitVector}" \
        --dry-run=client -o yaml | kubectl apply -f -
    
    # Apply Kubernetes manifests
    kubectl apply -f k8s-deployment.yaml
    
    echo "✅ Kubernetes deployment completed"
    echo "⏳ Waiting for deployment to be ready..."
    kubectl wait --for=condition=available --timeout=300s deployment/pitch-visualizer
    
    # Get the external IP (for LoadBalancer type service)
    EXTERNAL_IP=$(kubectl get service pitch-visualizer-service -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>/dev/null || echo "pending")
    echo "🌐 Application will be available at: http://$EXTERNAL_IP (or via Ingress)"
}

# Function to deploy for production with SSL
deploy_production() {
    echo "🔒 Deploying for production with SSL..."
    
    check_env_vars
    
    # Ensure SSL certificates exist
    if [ ! -d "ssl" ]; then
        echo "📁 Creating SSL directory..."
        mkdir ssl
        echo "⚠️  Please place your SSL certificates in ssl/ directory:"
        echo "   - ssl/cert.pem (certificate)"
        echo "   - ssl/key.pem (private key)"
        echo "   - ssl/chain.pem (certificate chain, optional)"
        exit 1
    fi
    
    # Deploy with Docker Compose including Nginx
    docker-compose -f docker-compose.yml down
    docker-compose -f docker-compose.yml up -d
    
    echo "✅ Production deployment completed"
    echo "🌐 HTTPS Application available at: https://your-domain.com"
}

# Function to run health checks
health_check() {
    echo "🏥 Running health checks..."
    
    if [ "$DEPLOYMENT_TYPE" = "docker" ]; then
        # Wait for container to start
        sleep 10
        
        # Check if the service is responding
        if curl -f http://localhost:8000/health > /dev/null 2>&1; then
            echo "✅ Health check passed"
            curl -s http://localhost:8000/health | jq .
        else
            echo "❌ Health check failed"
            exit 1
        fi
    elif [ "$DEPLOYMENT_TYPE" = "k8s" ]; then
        kubectl get pods -l app=pitch-visualizer
        kubectl logs -l app=pitch-visualizer --tail=20
    fi
}

# Main deployment logic
case $DEPLOYMENT_TYPE in
    "docker")
        deploy_docker
        ;;
    "k8s"|"kubernetes")
        deploy_k8s
        ;;
    "production"|"prod")
        deploy_production
        ;;
    *)
        echo "❌ Invalid deployment type: $DEPLOYMENT_TYPE"
        echo "Usage: $0 [docker|k8s|production] [development|production]"
        exit 1
        ;;
esac

# Run health checks
health_check

echo "🎉 Deployment completed successfully!"
echo ""
echo "📋 Next steps:"
echo "1. Test the application at http://localhost:8000"
echo "2. Check the API health at http://localhost:8000/health"
echo "3. Monitor logs with: docker-compose logs -f pitch-visualizer"
echo "4. For Kubernetes: kubectl logs -f deployment/pitch-visualizer"
