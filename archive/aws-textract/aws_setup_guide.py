#!/usr/bin/env python3
"""
AWS API Key Setup Guide

Since you have AWS Console access, this guide will help you create
the programmatic access keys needed for Textract API.
"""

def show_api_key_setup():
    print("🔑 AWS API Key Setup Guide")
    print("=" * 50)
    
    print("\nℹ️  You have AWS Console credentials, but Textract needs API keys")
    print("   Console login ≠ Programmatic API access")
    
    print("\n📋 STEP-BY-STEP GUIDE:")
    print("=" * 30)
    
    print("\n1️⃣  Login to AWS Console")
    print("   URL: https://899455913899.signin.aws.amazon.com/console")
    print("   Username: lambda-dev")
    print("   Password: qn5W50*$")
    
    print("\n2️⃣  Navigate to IAM")
    print("   • In AWS Console, search for 'IAM'")
    print("   • Click on 'IAM' service")
    
    print("\n3️⃣  Go to Users")
    print("   • Click 'Users' in left sidebar")
    print("   • Find your user 'lambda-dev'")
    print("   • Click on the username")
    
    print("\n4️⃣  Create Access Key")
    print("   • Click 'Security Credentials' tab")
    print("   • Scroll down to 'Access keys' section")
    print("   • Click 'Create access key'")
    
    print("\n5️⃣  Choose Use Case")
    print("   • Select 'Command Line Interface (CLI)'")
    print("   • Check confirmation checkbox")
    print("   • Click 'Next'")
    
    print("\n6️⃣  Add Description (Optional)")
    print("   • Description: 'Textract PDF Analysis'")
    print("   • Click 'Create access key'")
    
    print("\n7️⃣  SAVE THE KEYS! 🚨")
    print("   • Copy 'Access Key ID'")
    print("   • Copy 'Secret Access Key'")
    print("   • ⚠️  This is your ONLY chance to see the secret!")
    
    print("\n8️⃣  Update .env File")
    print("   Replace in .env:")
    print("   AWS_ACCESS_KEY_ID=your_copied_access_key_id")
    print("   AWS_SECRET_ACCESS_KEY=your_copied_secret_key")
    
    print("\n9️⃣  Check Permissions")
    print("   • In IAM Users → lambda-dev → Permissions")
    print("   • Look for 'AmazonTextractFullAccess' policy")
    print("   • If missing, click 'Add permissions' → 'Attach policies'")
    print("   • Search 'Textract' and attach 'AmazonTextractFullAccess'")
    
    print("\n🔟  Test Setup")
    print("   • Run: python validate_aws.py")
    print("   • Then: python textract_analyzer.py 1.pdf")
    
    print("\n" + "="*50)
    print("🎯 QUICK CHECKLIST:")
    print("□ Logged into AWS Console")
    print("□ Found IAM → Users → lambda-dev")  
    print("□ Created new Access Key")
    print("□ Copied both Access Key ID and Secret")
    print("□ Updated .env file with real keys")
    print("□ Verified Textract permissions attached")
    print("□ Tested with validation script")
    
    print("\n💡 TROUBLESHOOTING:")
    print("• If no 'Create access key' button → contact AWS admin")
    print("• If permission denied → need Textract policy attached")
    print("• If invalid token → keys might be wrong/expired")
    
    print("\n🎉 Once done, you'll have full Textract access!")

if __name__ == "__main__":
    show_api_key_setup()