#!/bin/bash

# AWS Deployment Script for EV Lead Generation Platform
# Cost-Effective Student Portfolio Deployment

set -e  # Exit on any error

# Configuration
PROJECT_NAME="ev-leadgen"
ENVIRONMENT="demo"
AWS_REGION="us-east-1"  # Cheapest region
STACK_NAME="${PROJECT_NAME}-${ENVIRONMENT}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
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
    
    success "Prerequisites check passed!"
}

# Set up billing alerts
setup_billing_alerts() {
    log "Setting up billing alerts..."
    
    read -p "Enter your email for billing alerts: " STUDENT_EMAIL
    
    if [[ ! "$STUDENT_EMAIL" =~ ^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$ ]]; then
        error "Invalid email format"
        exit 1
    fi
    
    # Enable billing alerts (requires root account)
    aws budgets create-budget \
        --account-id $(aws sts get-caller-identity --query Account --output text) \
        --budget '{
            "BudgetName": "'${PROJECT_NAME}'-budget",
            "BudgetLimit": {
                "Amount": "10.0",
                "Unit": "USD"
            },
            "TimeUnit": "MONTHLY",
            "BudgetType": "COST"
        }' \
        --notifications-with-subscribers '[
            {
                "Notification": {
                    "NotificationType": "ACTUAL",
                    "ComparisonOperator": "GREATER_THAN",
                    "Threshold": 80
                },
                "Subscribers": [
                    {
                        "SubscriptionType": "EMAIL",
                        "Address": "'${STUDENT_EMAIL}'"
                    }
                ]
            }
        ]' 2>/dev/null || warning "Budget already exists or insufficient permissions"
}

# Build and push Docker image
build_and_push_image() {
    log "Building and pushing Docker image..."
    
    # Get AWS account ID
    AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
    ECR_URI="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${PROJECT_NAME}"
    
    # Create ECR repository if it doesn't exist
    aws ecr describe-repositories --repository-names ${PROJECT_NAME} --region ${AWS_REGION} 2>/dev/null || \
    aws ecr create-repository --repository-name ${PROJECT_NAME} --region ${AWS_REGION}
    
    # Login to ECR
    aws ecr get-login-password --region ${AWS_REGION} | docker login --username AWS --password-stdin ${ECR_URI}
    
    # Build image
    log "Building Docker image..."
    docker build -t ${PROJECT_NAME}:latest .
    
    # Tag and push
    docker tag ${PROJECT_NAME}:latest ${ECR_URI}:latest
    docker push ${ECR_URI}:latest
    
    success "Docker image pushed to ECR: ${ECR_URI}:latest"
}

# Deploy CloudFormation stack
deploy_infrastructure() {
    log "Deploying AWS infrastructure..."
    
    # Deploy CloudFormation stack
    aws cloudformation deploy \
        --template-file aws/cloudformation-template.yml \
        --stack-name ${STACK_NAME} \
        --parameter-overrides \
            ProjectName=${PROJECT_NAME} \
            Environment=${ENVIRONMENT} \
            StudentEmail=${STUDENT_EMAIL} \
        --capabilities CAPABILITY_NAMED_IAM \
        --region ${AWS_REGION}
    
    success "Infrastructure deployed successfully!"
}

# Update Lambda function
update_lambda() {
    log "Updating Lambda function with new image..."
    
    AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
    ECR_URI="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${PROJECT_NAME}:latest"
    
    # Update Lambda function
    aws lambda update-function-code \
        --function-name ${PROJECT_NAME}-processor \
        --image-uri ${ECR_URI} \
        --region ${AWS_REGION}
    
    success "Lambda function updated!"
}

# Run a test execution
test_deployment() {
    log "Testing deployment..."
    
    # Get API Gateway URL
    API_URL=$(aws cloudformation describe-stacks \
        --stack-name ${STACK_NAME} \
        --query 'Stacks[0].Outputs[?OutputKey==`ApiGatewayURL`].OutputValue' \
        --output text \
        --region ${AWS_REGION})
    
    # Test API endpoint
    if curl -f -X POST "${API_URL}/process" -H "Content-Type: application/json" -d '{"test": true}' > /dev/null 2>&1; then
        success "API endpoint is responding!"
    else
        warning "API endpoint test failed, but deployment may still be successful"
    fi
    
    # Invoke Lambda directly for testing
    aws lambda invoke \
        --function-name ${PROJECT_NAME}-processor \
        --payload '{"test": true}' \
        --region ${AWS_REGION} \
        response.json > /dev/null
    
    if [ -f response.json ]; then
        success "Lambda function test completed!"
        rm response.json
    fi
}

# Display deployment information
show_deployment_info() {
    log "Deployment Information:"
    
    # Get stack outputs
    OUTPUTS=$(aws cloudformation describe-stacks \
        --stack-name ${STACK_NAME} \
        --query 'Stacks[0].Outputs' \
        --region ${AWS_REGION})
    
    echo -e "\n${GREEN}=== Deployment Complete ===${NC}"
    echo -e "${BLUE}Stack Name:${NC} ${STACK_NAME}"
    echo -e "${BLUE}Region:${NC} ${AWS_REGION}"
    echo -e "${BLUE}Estimated Cost:${NC} $0-5/month (mostly free tier)"
    
    echo -e "\n${YELLOW}Important URLs and Resources:${NC}"
    echo "$OUTPUTS" | jq -r '.[] | "\(.OutputKey): \(.OutputValue)"' 2>/dev/null || echo "Install jq for better output formatting"
    
    echo -e "\n${YELLOW}Next Steps:${NC}"
    echo "1. Check your email for billing alert confirmation"
    echo "2. Monitor costs in AWS Cost Explorer"
    echo "3. Run your data processing pipeline"
    echo "4. Document results for your portfolio"
    echo "5. Clean up resources when done: ./aws/cleanup.sh"
    
    echo -e "\n${RED}IMPORTANT:${NC} Remember to clean up resources to avoid charges!"
}

# Main deployment function
main() {
    echo -e "${GREEN}"
    echo "=========================================="
    echo "  EV Lead Generation AWS Deployment"
    echo "  Cost-Effective Student Portfolio"
    echo "=========================================="
    echo -e "${NC}"
    
    check_prerequisites
    setup_billing_alerts
    build_and_push_image
    deploy_infrastructure
    update_lambda
    test_deployment
    show_deployment_info
    
    success "Deployment completed successfully! 🚀"
    warning "Don't forget to clean up resources when you're done!"
}

# Handle script arguments
case "${1:-deploy}" in
    "deploy")
        main
        ;;
    "update")
        log "Updating deployment..."
        build_and_push_image
        update_lambda
        success "Update completed!"
        ;;
    "test")
        test_deployment
        ;;
    "info")
        show_deployment_info
        ;;
    *)
        echo "Usage: $0 [deploy|update|test|info]"
        echo "  deploy: Full deployment (default)"
        echo "  update: Update code only"
        echo "  test: Test deployment"
        echo "  info: Show deployment information"
        exit 1
        ;;
esac 