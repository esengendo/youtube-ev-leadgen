# EC2 Free Tier Deployment Guide
## YouTube EV Lead Generation Dashboard

This guide will help you deploy your Streamlit dashboard to AWS EC2 Free Tier in the **us-west-1** (Northern California) region.

## 🎯 What This Deployment Provides

- **Cost**: Completely FREE for 12 months (t2.micro instance, 750 hours/month)
- **After free tier**: Only ~$8.50/month
- **Perfect for**: Portfolio demonstrations and presentations
- **Persistent**: Your dashboard stays online 24/7
- **Professional**: Get a real AWS URL to showcase your work

## 📋 Prerequisites

Before running the deployment, ensure you have:

1. **AWS Account** with Free Tier eligibility
2. **AWS CLI** installed and configured
3. **Docker** installed and running
4. **SSH client** (built into macOS/Linux)

## 🚀 Quick Start

### Step 1: Configure AWS CLI
```bash
# Configure AWS CLI for us-west-1 region
aws configure
# Enter your:
# - AWS Access Key ID
# - AWS Secret Access Key  
# - Default region: us-west-1
# - Default output format: json
```

### Step 2: Navigate to Project Directory
```bash
cd /Users/baboo/Desktop/Project_AWS/youtube-ev-leadgen
```

### Step 3: Deploy to EC2
```bash
# Run the deployment script
./aws/ec2-deploy.sh deploy
```

The script will:
1. ✅ Check prerequisites (AWS CLI, Docker, credentials)
2. 🔑 Create EC2 key pair for secure access
3. 🛡️ Set up security group (SSH + HTTP access)
4. 🚀 Launch t2.micro EC2 instance (Free Tier)
5. 🐳 Build and transfer your Docker image
6. 📊 Deploy your Streamlit dashboard
7. 🧪 Test the deployment

## 📊 What You'll Get

After successful deployment:

```
🎉 Deployment completed successfully!

📊 Your YouTube EV Lead Generation Dashboard is now live!
🌐 URL: http://[YOUR-PUBLIC-IP]
🔑 SSH: ssh -i youtube-ev-leadgen-key.pem ec2-user@[YOUR-PUBLIC-IP]

💡 Tips:
  - The instance is running on AWS Free Tier (750 hours/month free for 12 months)
  - Your app will restart automatically if the instance reboots
  - To stop costs, you can stop the instance when not in use
  - To update your app, run: ./aws/ec2-deploy.sh update
```

## 🔧 Management Commands

### Update Your Application
```bash
./aws/ec2-deploy.sh update
```

### Clean Up Resources (when done)
```bash
./aws/ec2-deploy.sh cleanup
```

### Get Help
```bash
./aws/ec2-deploy.sh help
```

## 💰 Cost Management

### Free Tier Benefits (12 months)
- **EC2**: 750 hours/month of t2.micro instances
- **EBS**: 30 GB of storage
- **Data Transfer**: 15 GB outbound per month

### After Free Tier
- **t2.micro**: ~$8.50/month
- **EBS storage**: ~$3/month for 30GB
- **Data transfer**: $0.09/GB after 15GB

### Cost-Saving Tips
1. **Stop instance when not presenting**: 
   ```bash
   aws ec2 stop-instances --instance-ids [INSTANCE-ID] --region us-west-1
   ```

2. **Start instance when needed**:
   ```bash
   aws ec2 start-instances --instance-ids [INSTANCE-ID] --region us-west-1
   ```

3. **Monitor usage** in AWS Console → Billing Dashboard

## 🔍 Troubleshooting

### Common Issues

**1. "AWS credentials not configured"**
```bash
aws configure
# Enter your credentials and set region to us-west-1
```

**2. "Docker not found"**
```bash
# Install Docker Desktop for Mac
brew install --cask docker
```

**3. "Permission denied" for SSH key**
```bash
chmod 400 youtube-ev-leadgen-key.pem
```

**4. Dashboard not accessible**
- Wait 2-3 minutes for application to fully start
- Check security group allows HTTP traffic on port 80
- Verify instance is running in AWS Console

### Debug Commands
```bash
# Check instance status
aws ec2 describe-instances --region us-west-1

# SSH into instance to check logs
ssh -i youtube-ev-leadgen-key.pem ec2-user@[PUBLIC-IP]
docker logs streamlit-app
```

## 🌐 Accessing Your Dashboard

Once deployed, your dashboard will be available at:
- **URL**: `http://[YOUR-PUBLIC-IP]`
- **Features**: Full YouTube EV lead generation pipeline
- **Data**: Persistent storage on the EC2 instance
- **Updates**: Easy updates with the update command

## 🔒 Security Notes

- SSH key (`youtube-ev-leadgen-key.pem`) provides secure access
- Security group restricts access to necessary ports only
- Instance runs in public subnet for web access
- Consider setting up CloudFront for production use

## 📱 Next Steps

After deployment:
1. 🎯 Test all dashboard features
2. 📊 Run your lead generation pipeline
3. 💼 Add the URL to your portfolio/resume
4. 📈 Monitor AWS usage in billing console
5. 🔄 Update application as needed

## 🆘 Support

If you encounter issues:
1. Check the troubleshooting section above
2. Review AWS CloudWatch logs
3. SSH into the instance for direct debugging
4. Use `./aws/ec2-deploy.sh cleanup` to start fresh if needed

---

**Remember**: This deployment is perfect for portfolio demonstrations and costs almost nothing with AWS Free Tier! 🚀 