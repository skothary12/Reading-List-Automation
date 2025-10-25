#!/bin/bash
# Setup script for local configuration
# Copy this file to setup_local_config_private.sh and add your credentials there

echo "Setting up local configuration for Daily Reading Automation"
echo "============================================================"
echo ""
echo "⚠️  INSTRUCTIONS:"
echo "1. Copy this file: cp setup_local_config.sh setup_local_config_private.sh"
echo "2. Edit setup_local_config_private.sh and fill in your actual credentials"
echo "3. Run: source setup_local_config_private.sh"
echo "4. Run: python3 daily_reading.py"
echo ""
echo "Example configuration:"
echo ""
echo "export GOOGLE_DOC_URL=\"https://docs.google.com/document/d/YOUR_DOC_ID/edit\""
echo "export OPENAI_API_KEY=\"sk-proj-YOUR_API_KEY\""
echo "export EMAIL_TO=\"your-email@example.com\""
echo "export EMAIL_SMTP_SERVER=\"smtp.gmail.com\""
echo "export EMAIL_SMTP_PORT=\"587\""
echo "export EMAIL_ADDRESS=\"your-email@gmail.com\""
echo "export EMAIL_PASSWORD=\"your-gmail-app-password\""
