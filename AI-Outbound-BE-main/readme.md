## 🛠️ Setup Instructions
 Create and Activate Virtual Environment

It is **highly recommended** to use a virtual environment to isolate your dependencies.

### Using `venv`:

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate

# On macOS/Linux:
source venv/bin/activate
```

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Environment Variables
Create a .env file in the root directory and add your environment variables there. Example:

```env
FRONTEND_URL="FRONTEND_URL"
MONGO_DB_URL="MONGO_DB_URL"
RETELL_API_KEY="RETELL_API_KEY"
FROM_NUMBER = "FROM_NUMBER"
CALENDLY_API_KEY="CALENDLY_API_KEY"

SMTP_USER_EMAIL="SMTP_USER_EMAIL"
SMTP_PASSWORD="SMTP_PASSWORD"

GRAPH_API_TOKEN = "GRAPH_API_TOKEN"
GRAPH_URL = "GRAPH_URL"
```

###  Run the Server

```bash
uvicorn main:app --reload
```
- main refers to the file main.py
- app is the FastAPI instance inside main.py
- --reload enables hot-reloading (ideal for development)

### Run Cron 

```bash
python scripts/run_scheduler.py
```

## 🚀 Vercel Deployment

The application has been configured to deploy on Vercel without running cron jobs:

1. Push your project to a GitHub repository:
```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin your-repository-url
git push -u origin main
```

2. Connect your repository to Vercel:
   - Log in to [Vercel](https://vercel.com)
   - Click "Add New..." > "Project"
   - Select your GitHub repository
   - Vercel will automatically detect the Python project

3. Configure the deployment:
   - Set the framework preset to "Other"
   - Set the build command to `pip install -r requirements.txt`
   - Set the output directory to `.`
   - Set the install command to `pip install -r requirements.txt`

4. Set environment variables:
   - Scroll down to "Environment Variables" section
   - Add all required environment variables from your .env file
   - Make sure to add `VERCEL=1` to ensure cron jobs don't run

5. Deploy:
   - Click "Deploy"
   - Your API will be deployed without running cron jobs

**Note:** Cron jobs have been disabled in the Vercel deployment. To run scheduled tasks, set up a separate server or use a dedicated service like Heroku Scheduler or AWS Lambda with EventBridge.