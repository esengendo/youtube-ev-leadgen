# AWS Account Setup Guide
## For YouTube EV Lead Generation Dashboard Deployment

## 🎯 **What You Need to Set Up**

You don't need to create a "project" in AWS, but you do need proper credentials. Here's exactly what to do:

## 📋 **Step 1: Create AWS Account (if needed)**

1. Go to [aws.amazon.com](https://aws.amazon.com)
2. Click "Create an AWS Account"
3. Follow the signup process (requires credit card, but we'll stay in free tier)
4. Verify your email and phone number

## 🔑 **Step 2: Create IAM User for Programmatic Access**

### **Why IAM User?**
- Root account credentials are dangerous to use
- IAM user has limited, specific permissions
- Best security practice

### **Create IAM User:**

1. **Login to AWS Console**: [console.aws.amazon.com](https://console.aws.amazon.com)

2. **Navigate to IAM**:
   - Search for "IAM" in the top search bar
   - Click on "IAM" service

3. **Create User**:
   - Click "Users" in left sidebar
   - Click "Create user" button
   - **User name**: `youtube-ev-leadgen-deploy`
   - **Access type**: Select "Programmatic access"
   - Click "Next"

4. **Set Permissions**:
   - Click "Attach policies directly"
   - Search and select these policies:
     - ✅ `AmazonEC2FullAccess`
     - ✅ `IAMReadOnlyAccess` 
     - ✅ `AmazonS3FullAccess` (for future data storage)
   - Click "Next"

5. **Review and Create**:
   - Review the settings
   - Click "Create user"

6. **IMPORTANT - Save Credentials**:
   - ⚠️ **Download the CSV file** or copy the credentials
   - **Access Key ID**: `AKIA...` (starts with AKIA)
   - **Secret Access Key**: `...` (long random string)
   - ⚠️ **You can only see the Secret Access Key once!**

## 🛠️ **Step 3: Configure AWS CLI**

Once you have your credentials:

```bash
aws configure
```

Enter when prompted:
- **AWS Access Key ID**: `[Your Access Key from Step 2]`
- **AWS Secret Access Key**: `[Your Secret Key from Step 2]`
- **Default region name**: `us-west-1`
- **Default output format**: `json`

## ✅ **Step 4: Test Your Setup**

```bash
# This should return your account info without errors
aws sts get-caller-identity
```

Expected output:
```json
{
    "UserId": "AIDACKCEVSQ6C2EXAMPLE",
    "Account": "123456789012",
    "Arn": "arn:aws:iam::123456789012:user/youtube-ev-leadgen-deploy"
}
```

## 🚀 **Step 5: Deploy Your Application**

Now you can run the deployment:
```bash
./aws/ec2-deploy.sh deploy
```

## 🔒 **Security Best Practices**

### **What the IAM User Can Do:**
- ✅ Create/manage EC2 instances
- ✅ Create security groups and key pairs
- ✅ Access S3 for data storage
- ❌ Cannot delete your AWS account
- ❌ Cannot access billing information
- ❌ Limited to specific services

### **Keep Credentials Safe:**
- 🚫 Never commit credentials to Git
- 🚫 Never share credentials publicly
- ✅ Store securely on your local machine
- ✅ Use IAM users instead of root account

## 💰 **Free Tier Limits**

Your IAM user will use these free tier resources:
- **EC2**: 750 hours/month of t2.micro (enough for 24/7 for 1 month)
- **EBS**: 30 GB of storage
- **Data Transfer**: 15 GB outbound per month

## 🆘 **Troubleshooting**

### **"InvalidClientTokenId" Error**
- Credentials are wrong or expired
- Re-run `aws configure` with correct credentials

### **"Access Denied" Errors**
- IAM user needs more permissions
- Add the required policies in IAM console

### **"Region Not Supported" Errors**
- Make sure region is set to `us-west-1`
- Some AWS services aren't available in all regions

## 📞 **Need Help?**

Common issues:
1. **Forgot Secret Access Key**: Create new access key in IAM console
2. **Wrong Region**: Run `aws configure` again and set `us-west-1`
3. **Permission Issues**: Add more IAM policies as needed

---

**Next Step**: Once AWS CLI is configured, run `./aws/ec2-deploy.sh deploy` to deploy your dashboard! 🚀 