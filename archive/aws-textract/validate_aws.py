#!/usr/bin/env python3
"""
AWS Textract Credential Validator

This script helps diagnose AWS credential and permission issues.
"""

import boto3
import json
import os
from dotenv import load_dotenv

load_dotenv()

def validate_aws_credentials():
    """Validate AWS credentials and permissions"""
    
    print("🔍 AWS Textract Credential Validator")
    print("=" * 50)
    
    # Check if credentials are present
    aws_access_key = os.getenv('AWS_ACCESS_KEY_ID')
    aws_secret_key = os.getenv('AWS_SECRET_ACCESS_KEY')
    aws_region = os.getenv('AWS_REGION', 'us-east-1')
    
    if not aws_access_key or not aws_secret_key:
        print("❌ No AWS credentials found in .env file")
        print("\n📝 Please add to .env:")
        print("AWS_ACCESS_KEY_ID=your_access_key")
        print("AWS_SECRET_ACCESS_KEY=your_secret_key")
        print("AWS_REGION=us-east-1")
        return False
    
    print(f"✅ Credentials found in .env file")
    print(f"🔑 Access Key: {aws_access_key[:10]}...")
    print(f"🌍 Region: {aws_region}")
    
    # Test basic AWS connection
    print("\n🔗 Testing AWS connection...")
    try:
        # Test STS (Security Token Service) to validate credentials
        sts = boto3.client(
            'sts',
            aws_access_key_id=aws_access_key,
            aws_secret_access_key=aws_secret_key,
            region_name=aws_region
        )
        
        identity = sts.get_caller_identity()
        print(f"✅ AWS connection successful")
        print(f"👤 User ARN: {identity.get('Arn', 'N/A')}")
        print(f"🆔 Account: {identity.get('Account', 'N/A')}")
        
    except Exception as e:
        print(f"❌ AWS connection failed: {e}")
        print("\n🔧 Possible solutions:")
        print("1. Check if credentials are correct")
        print("2. Ensure AWS account is active")
        print("3. Try generating new access keys")
        return False
    
    # Test Textract permissions
    print("\n📄 Testing Textract permissions...")
    try:
        textract = boto3.client(
            'textract',
            aws_access_key_id=aws_access_key,
            aws_secret_access_key=aws_secret_key,
            region_name=aws_region
        )
        
        # Try to list available operations (this requires minimal permissions)
        # We'll do a simple service check
        print("✅ Textract client created successfully")
        
        # Test with a minimal operation to check permissions
        try:
            # This will fail but should give us permission info
            textract.detect_document_text(Document={'Bytes': b'test'})
        except Exception as perm_error:
            error_str = str(perm_error)
            if 'UnrecognizedClientException' in error_str:
                print("❌ Invalid credentials or token")
                print("🔧 Solution: Generate new AWS access keys")
            elif 'AccessDenied' in error_str:
                print("❌ Access denied - insufficient permissions")
                print("🔧 Solution: Add AmazonTextractFullAccess policy to IAM user")
            elif 'InvalidDocument' in error_str:
                print("✅ Textract permissions OK (test document was invalid as expected)")
                return True
            else:
                print(f"⚠️  Unknown permission error: {error_str}")
    
    except Exception as e:
        print(f"❌ Textract client creation failed: {e}")
        return False
    
    return True

def show_setup_instructions():
    """Show detailed setup instructions"""
    
    print("\n" + "="*60)
    print("🛠️  AWS SETUP INSTRUCTIONS")
    print("="*60)
    
    print("\n1️⃣  CREATE AWS ACCOUNT")
    print("   • Go to https://aws.amazon.com/")
    print("   • Sign up for free account")
    print("   • Verify email and add payment method")
    
    print("\n2️⃣  CREATE IAM USER")
    print("   • Go to AWS Console → IAM → Users")
    print("   • Click 'Create user'")
    print("   • Username: textract-user")
    print("   • Select 'Programmatic access'")
    
    print("\n3️⃣  ATTACH PERMISSIONS")
    print("   • Click 'Attach policies directly'")
    print("   • Search for 'AmazonTextractFullAccess'")
    print("   • Select and attach the policy")
    
    print("\n4️⃣  CREATE ACCESS KEYS")
    print("   • Go to user → Security Credentials tab")
    print("   • Click 'Create access key'")
    print("   • Choose 'Command Line Interface (CLI)'")
    print("   • Confirm and create")
    
    print("\n5️⃣  UPDATE .ENV FILE")
    print("   • Copy Access Key ID and Secret Key")
    print("   • Update .env file with actual values")
    print("   • Keep credentials secure!")
    
    print("\n💰 COST INFO")
    print("   • First 1,000 pages/month FREE for 12 months")
    print("   • After free tier: $1.50 per 1,000 pages")
    print("   • Your test file will cost ~$0.0015")

def main():
    print("🚀 Starting AWS Textract validation...")
    
    valid = validate_aws_credentials()
    
    if not valid:
        show_setup_instructions()
        print("\n❌ Please fix AWS setup and try again")
    else:
        print("\n✅ AWS Textract is ready to use!")
        print("🎉 Run: python textract_analyzer.py 1.pdf")

if __name__ == "__main__":
    main()