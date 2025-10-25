# How to Add Multiple Email Recipients

You can now send the daily reading digest to multiple email addresses!

## Method 1: Comma-Separated List (Recommended)

Simply separate email addresses with commas in your configuration.

### For GitHub Actions

Update your `EMAIL_TO` secret:

1. Go to: https://github.com/skothary12/Reading-List-Automation/settings/secrets/actions
2. Click on `EMAIL_TO`
3. Click "Update secret"
4. Enter comma-separated emails:
   ```
   email1@example.com, email2@example.com, email3@example.com
   ```
5. Click "Update secret"

### For Local Testing (config.json)

```json
{
  "email": {
    "to": "email1@example.com, email2@example.com, email3@example.com",
    "smtp": {
      ...
    }
  }
}
```

### For Local Testing (Environment Variables)

```bash
export EMAIL_TO="email1@example.com, email2@example.com, email3@example.com"
```

---

## Examples

### Two Recipients
```
alice@example.com, bob@example.com
```

### Three Recipients
```
alice@example.com, bob@example.com, charlie@example.com
```

### With Spaces (optional - automatically cleaned)
```
alice@example.com , bob@example.com , charlie@example.com
```

---

## How It Works

The code automatically:
1. Splits the string by commas
2. Trims whitespace from each email
3. Sends one email to all recipients
4. All recipients see each other in the "To:" field

---

## Privacy Note

All recipients will see each other's email addresses in the "To:" field.

If you want to hide recipients from each other (BCC), let me know and I can implement that!

---

## Testing

To test with multiple recipients locally:

```bash
export GOOGLE_DOC_URL="your-doc-url"
export OPENAI_API_KEY="your-key"
export EMAIL_TO="recipient1@example.com, recipient2@example.com"
export EMAIL_SMTP_SERVER="smtp.gmail.com"
export EMAIL_SMTP_PORT="587"
export EMAIL_ADDRESS="your-email@gmail.com"
export EMAIL_PASSWORD="your-app-password"

python3 daily_reading.py
```

Both recipients should receive the same email!
