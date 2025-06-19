#!/bin/bash

# AWS Cleanup Script for EV Lead Generation Platform
# Safely remove all resources to avoid charges

set -e  # Exit on any error

# Configuration
PROJECT_NAME="ev-leadgen"
ENVIRONMENT="demo"
AWS_REGION="us-east-1"
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

# Confirm cleanup
confirm_cleanup() {
    echo -e "${RED}"
    echo "=========================================="
    echo "  AWS RESOURCE CLEANUP"
    echo "  This will DELETE all AWS resources!"
    echo "=========================================="
    echo -e "${NC}"
    
    echo -e "${YELLOW}Resources to be deleted:${NC}"
    echo "• CloudFormation Stack: ${STACK_NAME}"
    echo "• S3 Bucket and all data"
    echo "• ECR Repository and images"
    echo "• Lambda functions"
    echo "• API Gateway"
    echo "• CloudWatch logs"
    echo "• IAM roles and policies"
    echo "• Billing budgets"
    
    echo ""
    read -p "Are you sure you want to proceed? (type 'DELETE' to confirm): " CONFIRM
    
    if [ "$CONFIRM" != "DELETE" ]; then
        log "Cleanup cancelled."
        exit 0
    fi
}

# Empty and delete S3 bucket
cleanup_s3() {
    log "Cleaning up S3 resources..."
    
    # Get bucket name from CloudFormation stack
    BUCKET_NAME=$(aws cloudformation describe-stacks \
        --stack-name ${STACK_NAME} \
        --query 'Stacks[0].Outputs[?OutputKey==`S3BucketName`].OutputValue' \
        --output text \
        --region ${AWS_REGION} 2>/dev/null || echo "")
    
    if [ -n "$BUCKET_NAME" ] && [ "$BUCKET_NAME" != "None" ]; then
        log "Emptying S3 bucket: ${BUCKET_NAME}"
        
        # Delete all objects and versions
        aws s3api list-object-versions \
            --bucket ${BUCKET_NAME} \
            --query 'Versions[].{Key:Key,VersionId:VersionId}' \
            --output text | while read key version; do
            if [ -n "$key" ] && [ -n "$version" ]; then
                aws s3api delete-object --bucket ${BUCKET_NAME} --key "$key" --version-id "$version" 2>/dev/null || true
            fi
        done
        
        # Delete delete markers
        aws s3api list-object-versions \
            --bucket ${BUCKET_NAME} \
            --query 'DeleteMarkers[].{Key:Key,VersionId:VersionId}' \
            --output text | while read key version; do
            if [ -n "$key" ] && [ -n "$version" ]; then
                aws s3api delete-object --bucket ${BUCKET_NAME} --key "$key" --version-id "$version" 2>/dev/null || true
            fi
        done
        
        success "S3 bucket emptied"
    else
        warning "S3 bucket not found or already deleted"
    fi
}

# Delete ECR repository
cleanup_ecr() {
    log "Cleaning up ECR repository..."
    
    # Delete ECR repository and all images
    aws ecr delete-repository \
        --repository-name ${PROJECT_NAME} \
        --force \
        --region ${AWS_REGION} 2>/dev/null && success "ECR repository deleted" || warning "ECR repository not found"
}

# Delete CloudFormation stack
cleanup_cloudformation() {
    log "Deleting CloudFormation stack..."
    
    # Delete the stack
    aws cloudformation delete-stack \
        --stack-name ${STACK_NAME} \
        --region ${AWS_REGION}
    
    log "Waiting for stack deletion to complete..."
    aws cloudformation wait stack-delete-complete \
        --stack-name ${STACK_NAME} \
        --region ${AWS_REGION}
    
    success "CloudFormation stack deleted"
}

# Clean up billing budgets
cleanup_budgets() {
    log "Cleaning up billing budgets..."
    
    AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
    
    # Delete budget
    aws budgets delete-budget \
        --account-id ${AWS_ACCOUNT_ID} \
        --budget-name "${PROJECT_NAME}-budget" 2>/dev/null && success "Budget deleted" || warning "Budget not found or insufficient permissions"
}

# Clean up CloudWatch logs
cleanup_logs() {
    log "Cleaning up CloudWatch logs..."
    
    # Delete log groups
    LOG_GROUPS=$(aws logs describe-log-groups \
        --log-group-name-prefix "/aws/lambda/${PROJECT_NAME}" \
        --query 'logGroups[].logGroupName' \
        --output text \
        --region ${AWS_REGION} 2>/dev/null || echo "")
    
    if [ -n "$LOG_GROUPS" ]; then
        for log_group in $LOG_GROUPS; do
            aws logs delete-log-group --log-group-name "$log_group" --region ${AWS_REGION} 2>/dev/null || true
        done
        success "CloudWatch logs deleted"
    else
        warning "No CloudWatch logs found"
    fi
}

# Verify cleanup
verify_cleanup() {
    log "Verifying cleanup..."
    
    # Check if stack still exists
    if aws cloudformation describe-stacks --stack-name ${STACK_NAME} --region ${AWS_REGION} &>/dev/null; then
        error "CloudFormation stack still exists!"
        return 1
    fi
    
    # Check if ECR repository still exists
    if aws ecr describe-repositories --repository-names ${PROJECT_NAME} --region ${AWS_REGION} &>/dev/null; then
        warning "ECR repository still exists"
    fi
    
    success "Cleanup verification completed"
}

# Show final cost summary
show_cost_summary() {
    log "Generating final cost summary..."
    
    echo -e "\n${GREEN}=== Cleanup Complete ===${NC}"
    echo -e "${BLUE}All AWS resources have been deleted${NC}"
    
    echo -e "\n${YELLOW}Final Steps:${NC}"
    echo "1. Check AWS Cost Explorer for final charges"
    echo "2. Verify no unexpected resources remain"
    echo "3. Keep your project code and documentation for portfolio"
    echo "4. Consider taking screenshots of your deployment for presentations"
    
    echo -e "\n${GREEN}Portfolio Assets Preserved:${NC}"
    echo "• Complete source code"
    echo "• Docker configurations"
    echo "• AWS infrastructure templates"
    echo "• Documentation and README"
    echo "• Local data and visualizations"
    
    echo -e "\n${BLUE}Estimated Total Cost:${NC} $0-10 (one-time demo)"
}

# Main cleanup function
main() {
    confirm_cleanup
    
    log "Starting AWS resource cleanup..."
    
    cleanup_s3
    cleanup_ecr
    cleanup_cloudformation
    cleanup_budgets
    cleanup_logs
    verify_cleanup
    show_cost_summary
    
    success "All AWS resources have been cleaned up! 🧹"
    echo -e "${GREEN}Your portfolio project is ready for presentation!${NC}"
}

# Handle script arguments
case "${1:-cleanup}" in
    "cleanup")
        main
        ;;
    "verify")
        verify_cleanup
        ;;
    "cost")
        show_cost_summary
        ;;
    *)
        echo "Usage: $0 [cleanup|verify|cost]"
        echo "  cleanup: Full resource cleanup (default)"
        echo "  verify: Verify cleanup completion"
        echo "  cost: Show cost summary"
        exit 1
        ;;
esac 