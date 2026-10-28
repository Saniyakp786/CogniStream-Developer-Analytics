# Testing Guide

Run project tests using:

python -m pytest tests -v

Review test results and resolve failures before submitting changes.

# Troubleshooting Guide

## Common Issues

### 1. Missing Dependencies
Install the project dependencies using:

`python -m pip install -r requirements.txt`

### 2. Missing API Key
Check that the required environment variables are configured in your local `.env` file.

Never upload real API keys to GitHub.

### 3. Application Does Not Start
- Confirm that the terminal is open in the project root.
- Verify that the virtual environment is activated.
- Check the terminal output for missing packages or configuration errors.

### 4. No Results Returned
- Verify that the uploaded documents contain readable text.
- Check that the question is relevant to the available data.
- Review the application's retrieval configuration.

If the issue continues, review the application logs for more details.