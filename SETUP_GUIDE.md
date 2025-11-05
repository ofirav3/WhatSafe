# WhatSafe - Complete Setup Guide

This guide will walk you through setting up and running WhatSafe with all the new AI features.

## Prerequisites

- Python 3.9 or higher
- Internet connection (for installing dependencies)
- OpenAI API key (optional, for AI-powered analysis)

## Step-by-Step Setup

### Step 1: Navigate to the Project Directory

```bash
cd "/Users/ofir/Desktop/ עבודה/WhatSafe"
```

### Step 2: Create a Virtual Environment

```bash
python3 -m venv .venv
```

This creates an isolated Python environment for the project.

### Step 3: Activate the Virtual Environment

**On macOS/Linux:**
```bash
source .venv/bin/activate
```

**On Windows:**
```bash
.venv\Scripts\activate
```

You should see `(.venv)` at the beginning of your terminal prompt.

### Step 4: Upgrade pip

```bash
pip install --upgrade pip
```

### Step 5: Install Dependencies

```bash
pip install -r requirements.txt
```

This installs:
- FastAPI (web framework)
- Uvicorn (ASGI server)
- httpx (HTTP client)
- python-multipart (file uploads)
- pandas (data tables)
- **openai** (OpenAI API client) - NEW
- **python-dotenv** (environment variables) - NEW

### Step 6: Set Up OpenAI API Key (Optional but Recommended)

**Option A: Using a .env file (Recommended)**

1. Create a file named `.env` in the project root directory:
   ```bash
   touch .env
   ```

2. Open the `.env` file and add your OpenAI API key:
   ```
   OPENAI_API_KEY=your-api-key-here
   ```

   Replace `your-api-key-here` with your actual OpenAI API key.
   
   **To get an OpenAI API key:**
   - Go to https://platform.openai.com/api-keys
   - Sign up or log in
   - Click "Create new secret key"
   - Copy the key and paste it in the `.env` file

**Option B: Using Environment Variable**

```bash
export OPENAI_API_KEY=your-api-key-here
```

**Note:** If you don't set up the API key, the keyword-based analysis will still work, but the AI analysis feature will be unavailable.

### Step 7: Start the Detection Service

Open your first terminal window and run:

```bash
# Make sure you're in the project directory and virtual environment is activated
./.venv/bin/python detection_service.py
```

You should see:
```
Starting Whatsafe Detection Service on http://0.0.0.0:8001 …
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8001
```

**Keep this terminal window open!** The detection service must be running.

### Step 8: Start the UI Service

Open a **second terminal window** and run:

```bash
# Navigate to the project directory again
cd "/Users/ofir/Desktop/ עבודה/WhatSafe"

# Activate the virtual environment
source .venv/bin/activate

# Start the UI service
./.venv/bin/python ui_service.py
```

You should see:
```
Starting Whatsafe UI Service on http://0.0.0.0:8002 …
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8002
```

**Keep this terminal window open too!**

### Step 9: Open the Application

Open your web browser and go to:

```
http://localhost:8002
```

You should see the WhatSafe upload form with:
- File upload button
- "Analyze" button
- **NEW:** Checkbox for "Also analyze with AI (OpenAI) for detailed insights"

## How to Use

### Basic Analysis (Keyword-Based)

1. Click "Choose File" and select a WhatsApp `.txt` export file
2. Click "Analyze"
3. You'll see the keyword-based analysis results

### AI-Powered Analysis (Enhanced)

1. Click "Choose File" and select a WhatsApp `.txt` export file
2. **Check the box** "Also analyze with AI (OpenAI) for detailed insights"
3. Click "Analyze"
4. Wait for both analyses to complete (AI takes a bit longer)
5. You'll see:
   - Standard keyword-based analysis (top section)
   - **AI-powered analysis details** (bottom section with gradient background)
     - AI Detection status
     - Confidence Score
     - AI Risk Level
     - AI Reasoning
     - Detailed Findings
     - Potential Targets

### Test with Sample File

You can test with the included sample file:

```bash
# The file is already in the project:
whatsapp_group_sample.txt
```

Just upload it through the web interface!

## Troubleshooting

### Issue: "Detection Service Unavailable"

**Solution:** Make sure the Detection Service is running on port 8001. Check your first terminal window.

### Issue: "AI analysis unavailable"

**Possible causes:**
1. OpenAI API key not set up - Check your `.env` file or environment variable
2. API key is invalid - Verify your key at https://platform.openai.com/api-keys
3. Network issues - Check your internet connection
4. OpenAI API quota exceeded - Check your OpenAI account usage

**Solution:** The keyword-based analysis will still work. Fix the API key issue to enable AI features.

### Issue: Import errors when starting services

**Solution:** Make sure you:
1. Created and activated the virtual environment
2. Installed all dependencies: `pip install -r requirements.txt`

### Issue: Port already in use

**Solution:** 
- Port 8001 is used by Detection Service
- Port 8002 is used by UI Service
- Close any other applications using these ports, or change the ports in the code

## Stopping the Services

Press `Ctrl+C` in each terminal window to stop the services gracefully.

## Next Steps

- Try analyzing different WhatsApp exports
- Compare keyword-based vs AI analysis results
- Check the API documentation at http://localhost:8001/docs (FastAPI auto-generated docs)

## API Endpoints

### Keyword-Based Analysis
```bash
curl -X POST http://localhost:8001/api/analyze-text \
  -H "Content-Type: application/json" \
  -d '{"content":"your whatsapp text here"}'
```

### AI-Powered Analysis
```bash
curl -X POST http://localhost:8001/api/analyze-text-ai \
  -H "Content-Type: application/json" \
  -d '{"content":"your whatsapp text here"}'
```

## Summary

✅ **What's New:**
- OpenAI API integration for advanced AI analysis
- Enhanced UI with AI analysis details section
- Optional AI analysis checkbox in upload form
- Graceful error handling if AI is unavailable

✅ **What Still Works:**
- Keyword-based analysis (fast, no API key needed)
- All existing features
- UI and charts

Enjoy analyzing your WhatsApp group chats! 🚀

