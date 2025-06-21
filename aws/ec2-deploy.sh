#!/bin/bash

# EC2 Free Tier Deployment Script for YouTube EV Lead Generation Dashboard
# Optimized for cost-effective student portfolio deployment

set -e  # Exit on any error

# Configuration
PROJECT_NAME="youtube-ev-leadgen"
ENVIRONMENT="demo"
AWS_REGION="us-west-1"  # Northern California region
INSTANCE_TYPE="t2.micro"  # Free tier eligible
KEY_NAME="${PROJECT_NAME}-key"
SECURITY_GROUP_NAME="${PROJECT_NAME}-sg"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    log "Checking prerequisites..."
    
    # Check AWS CLI
    if ! command -v aws &> /dev/null; then
        error "AWS CLI not found. Please install it first."
        exit 1
    fi
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        error "Docker not found. Please install it first."
        exit 1
    fi
    
    # Check AWS credentials
    if ! aws sts get-caller-identity &> /dev/null; then
        error "AWS credentials not configured. Run 'aws configure' first."
        exit 1
    fi
    
    # Check if we're in the right directory
    if [[ ! -f "Dockerfile" ]]; then
        error "Dockerfile not found. Please run this script from the project root."
        exit 1
    fi
    
    success "Prerequisites check passed!"
}

# Create EC2 Key Pair
create_key_pair() {
    log "Creating EC2 Key Pair..."
    
    # Check if key pair already exists
    if aws ec2 describe-key-pairs --key-names ${KEY_NAME} --region ${AWS_REGION} &> /dev/null; then
        warning "Key pair ${KEY_NAME} already exists. Skipping creation."
        return 0
    fi
    
    # Create key pair and save to file
    aws ec2 create-key-pair \
        --key-name ${KEY_NAME} \
        --region ${AWS_REGION} \
        --query 'KeyMaterial' \
        --output text > ${KEY_NAME}.pem
    
    # Set proper permissions
    chmod 400 ${KEY_NAME}.pem
    
    success "Key pair created: ${KEY_NAME}.pem"
    warning "IMPORTANT: Save ${KEY_NAME}.pem file securely. You'll need it to connect to your instance."
}

# Create Security Group
create_security_group() {
    log "Creating Security Group..."
    
    # Check if security group already exists
    if aws ec2 describe-security-groups --group-names ${SECURITY_GROUP_NAME} --region ${AWS_REGION} &> /dev/null; then
        warning "Security group ${SECURITY_GROUP_NAME} already exists. Skipping creation."
        return 0
    fi
    
    # Create security group
    SECURITY_GROUP_ID=$(aws ec2 create-security-group \
        --group-name ${SECURITY_GROUP_NAME} \
        --description "Security group for ${PROJECT_NAME} Streamlit dashboard" \
        --region ${AWS_REGION} \
        --query 'GroupId' \
        --output text)
    
    # Add SSH access (port 22)
    aws ec2 authorize-security-group-ingress \
        --group-id ${SECURITY_GROUP_ID} \
        --protocol tcp \
        --port 22 \
        --cidr 0.0.0.0/0 \
        --region ${AWS_REGION}
    
    # Add HTTP access (port 80) for Streamlit
    aws ec2 authorize-security-group-ingress \
        --group-id ${SECURITY_GROUP_ID} \
        --protocol tcp \
        --port 80 \
        --cidr 0.0.0.0/0 \
        --region ${AWS_REGION}
    
    # Add Streamlit access (port 8501) as backup
    aws ec2 authorize-security-group-ingress \
        --group-id ${SECURITY_GROUP_ID} \
        --protocol tcp \
        --port 8501 \
        --cidr 0.0.0.0/0 \
        --region ${AWS_REGION}
    
    success "Security group created: ${SECURITY_GROUP_ID}"
}

# Launch EC2 Instance
launch_ec2_instance() {
    log "Launching EC2 Instance..."
    
    # Get the latest Amazon Linux 2023 AMI
    AMI_ID=$(aws ec2 describe-images \
        --owners amazon \
        --filters "Name=name,Values=al2023-ami-*" "Name=architecture,Values=x86_64" "Name=state,Values=available" \
        --query 'Images | sort_by(@, &CreationDate) | [-1].ImageId' \
        --output text \
        --region ${AWS_REGION})
    
    log "Using AMI: ${AMI_ID}"
    
    # Create user data script for automatic setup
    cat > user-data.sh << 'EOF'
#!/bin/bash
yum update -y
yum install -y docker git

# Start Docker service
systemctl start docker
systemctl enable docker
usermod -a -G docker ec2-user

# Install Docker Compose
curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# Create application directory
mkdir -p /home/ec2-user/app
chown ec2-user:ec2-user /home/ec2-user/app

# Create a simple startup script
cat > /home/ec2-user/start-app.sh << 'SCRIPT'
#!/bin/bash
cd /home/ec2-user/app
# Stop any existing container
docker stop streamlit-app 2>/dev/null || true
docker rm streamlit-app 2>/dev/null || true
# Run the new container
docker run -d --name streamlit-app --restart unless-stopped -p 80:8501 youtube-ev-leadgen:latest
SCRIPT

chmod +x /home/ec2-user/start-app.sh
chown ec2-user:ec2-user /home/ec2-user/start-app.sh

# Signal that setup is complete
touch /home/ec2-user/setup-complete
EOF

    # Launch instance
    INSTANCE_ID=$(aws ec2 run-instances \
        --image-id ${AMI_ID} \
        --count 1 \
        --instance-type ${INSTANCE_TYPE} \
        --key-name ${KEY_NAME} \
        --security-groups ${SECURITY_GROUP_NAME} \
        --user-data file://user-data.sh \
        --tag-specifications "ResourceType=instance,Tags=[{Key=Name,Value=${PROJECT_NAME}-dashboard},{Key=Project,Value=${PROJECT_NAME}},{Key=Environment,Value=${ENVIRONMENT}}]" \
        --region ${AWS_REGION} \
        --query 'Instances[0].InstanceId' \
        --output text)
    
    # Clean up user data file
    rm user-data.sh
    
    success "EC2 Instance launched: ${INSTANCE_ID}"
    log "Waiting for instance to be running..."
    
    # Wait for instance to be running
    aws ec2 wait instance-running --instance-ids ${INSTANCE_ID} --region ${AWS_REGION}
    
    # Get public IP
    PUBLIC_IP=$(aws ec2 describe-instances \
        --instance-ids ${INSTANCE_ID} \
        --region ${AWS_REGION} \
        --query 'Reservations[0].Instances[0].PublicIpAddress' \
        --output text)
    
    success "Instance is running! Public IP: ${PUBLIC_IP}"
    
    # Save instance info
    cat > instance-info.txt << EOF
Instance ID: ${INSTANCE_ID}
Public IP: ${PUBLIC_IP}
Key Pair: ${KEY_NAME}.pem
Security Group: ${SECURITY_GROUP_NAME}
Region: ${AWS_REGION}

SSH Command:
ssh -i ${KEY_NAME}.pem ec2-user@${PUBLIC_IP}

Dashboard URL (after deployment):
http://${PUBLIC_IP}
EOF

    success "Instance information saved to instance-info.txt"
}

# Build and transfer Docker image
deploy_application() {
    log "Building and deploying application..."
    
    # Get instance info
    if [[ ! -f "instance-info.txt" ]]; then
        error "instance-info.txt not found. Please run the launch step first."
        exit 1
    fi
    
    PUBLIC_IP=$(grep "Public IP:" instance-info.txt | cut -d' ' -f3)
    
    # Build Docker image
    log "Building Docker image..."
    docker build -t youtube-ev-leadgen:latest .
    
    # Save Docker image to tar file
    log "Saving Docker image to file..."
    docker save youtube-ev-leadgen:latest | gzip > youtube-ev-leadgen.tar.gz
    
    # Wait for instance to be fully ready
    log "Waiting for instance to be ready (this may take a few minutes)..."
    sleep 60
    
    # Check if instance is ready by waiting for SSH
    for i in {1..30}; do
        if ssh -i ${KEY_NAME}.pem -o ConnectTimeout=5 -o StrictHostKeyChecking=no ec2-user@${PUBLIC_IP} "echo 'ready'" &> /dev/null; then
            success "Instance is ready for deployment!"
            break
        fi
        log "Waiting for instance to be ready... (attempt $i/30)"
        sleep 10
    done
    
    # Transfer Docker image
    log "Transferring Docker image to EC2..."
    scp -i ${KEY_NAME}.pem -o StrictHostKeyChecking=no youtube-ev-leadgen.tar.gz ec2-user@${PUBLIC_IP}:/home/ec2-user/app/
    
    # Load and run Docker image on EC2
    log "Loading and running Docker image on EC2..."
    ssh -i ${KEY_NAME}.pem -o StrictHostKeyChecking=no ec2-user@${PUBLIC_IP} << 'REMOTE_SCRIPT'
cd /home/ec2-user/app
# Load Docker image
gunzip -c youtube-ev-leadgen.tar.gz | docker load
# Run the application
./start-app.sh
# Check if container is running
sleep 5
if docker ps | grep -q streamlit-app; then
    echo "✅ Streamlit app is running successfully!"
else
    echo "❌ Failed to start Streamlit app"
    docker logs streamlit-app
fi
REMOTE_SCRIPT

    # Clean up local tar file
    rm youtube-ev-leadgen.tar.gz
    
    success "Application deployed successfully!"
    log "Your Streamlit dashboard should be available at: http://${PUBLIC_IP}"
    warning "Note: It may take a few minutes for the application to fully start."
}

# Test deployment
test_deployment() {
    log "Testing deployment..."
    
    PUBLIC_IP=$(grep "Public IP:" instance-info.txt | cut -d' ' -f3)
    
    # Test HTTP endpoint
    for i in {1..10}; do
        if curl -f -s "http://${PUBLIC_IP}" > /dev/null; then
            success "✅ Dashboard is accessible at http://${PUBLIC_IP}"
            return 0
        fi
        log "Testing connectivity... (attempt $i/10)"
        sleep 10
    done
    
    warning "Dashboard may still be starting up. Please check http://${PUBLIC_IP} in a few minutes."
}

# Cleanup function
cleanup() {
    log "Cleaning up resources..."
    
    if [[ -f "instance-info.txt" ]]; then
        INSTANCE_ID=$(grep "Instance ID:" instance-info.txt | cut -d' ' -f3)
        
        read -p "Do you want to terminate the EC2 instance ${INSTANCE_ID}? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            aws ec2 terminate-instances --instance-ids ${INSTANCE_ID} --region ${AWS_REGION}
            success "Instance ${INSTANCE_ID} termination initiated."
        fi
    fi
    
    read -p "Do you want to delete the key pair and security group? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        # Delete key pair
        aws ec2 delete-key-pair --key-name ${KEY_NAME} --region ${AWS_REGION} 2>/dev/null || true
        rm -f ${KEY_NAME}.pem
        
        # Delete security group
        aws ec2 delete-security-group --group-name ${SECURITY_GROUP_NAME} --region ${AWS_REGION} 2>/dev/null || true
        
        success "Resources cleaned up."
    fi
}

# Main deployment function
deploy() {
    log "Starting EC2 Free Tier deployment for ${PROJECT_NAME}..."
    
    check_prerequisites
    create_key_pair
    create_security_group
    launch_ec2_instance
    deploy_application
    test_deployment
    
    success "🎉 Deployment completed successfully!"
    echo
    echo "📊 Your YouTube EV Lead Generation Dashboard is now live!"
    echo "🌐 URL: http://$(grep "Public IP:" instance-info.txt | cut -d' ' -f3)"
    echo "🔑 SSH: ssh -i ${KEY_NAME}.pem ec2-user@$(grep "Public IP:" instance-info.txt | cut -d' ' -f3)"
    echo
    echo "💡 Tips:"
    echo "  - The instance is running on AWS Free Tier (750 hours/month free for 12 months)"
    echo "  - Your app will restart automatically if the instance reboots"
    echo "  - To stop costs, you can stop the instance when not in use"
    echo "  - To update your app, run: ./aws/ec2-deploy.sh update"
    echo
    warning "💰 Remember: Keep track of your AWS usage to stay within free tier limits!"
}

# Update function
update() {
    log "Updating application..."
    
    if [[ ! -f "instance-info.txt" ]]; then
        error "instance-info.txt not found. Please deploy first."
        exit 1
    fi
    
    deploy_application
    test_deployment
    success "Application updated successfully!"
}

# Show help
show_help() {
    echo "Usage: $0 [COMMAND]"
    echo
    echo "Commands:"
    echo "  deploy    - Deploy the application to EC2 (default)"
    echo "  update    - Update the application on existing EC2 instance"
    echo "  cleanup   - Clean up AWS resources"
    echo "  help      - Show this help message"
    echo
    echo "Examples:"
    echo "  $0 deploy   # Deploy new application"
    echo "  $0 update   # Update existing deployment"
    echo "  $0 cleanup  # Clean up resources"
}

# Main script logic
case "${1:-deploy}" in
    "deploy")
        deploy
        ;;
    "update")
        update
        ;;
    "cleanup")
        cleanup
        ;;
    "help"|"-h"|"--help")
        show_help
        ;;
    *)
        error "Unknown command: $1"
        show_help
        exit 1
        ;;
esac 