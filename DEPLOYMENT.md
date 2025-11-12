# Vercel Deployment Guide (GitHub)

This guide will help you deploy the Research Chatbot to Vercel via GitHub.

## Prerequisites

- GitHub account with the repository pushed
- Vercel account (sign up at https://vercel.com)

## Deployment Steps

### 1. Connect Repository to Vercel

1. Go to [Vercel Dashboard](https://vercel.com/dashboard)
2. Click **"Add New Project"**
3. Import your GitHub repository
4. Vercel will automatically detect the Python project

### 2. Configure Environment Variables

**IMPORTANT**: Set these environment variables in Vercel before deploying:

1. In the Vercel project settings, go to **"Environment Variables"**
2. Add the following three variables:

   - **Name**: `FLASK_SECRET_KEY`
     - **Value**: A strong random secret key (e.g., generate one using: `python -c "import secrets; print(secrets.token_hex(32))"`)
   
   - **Name**: `OPENAI_API_KEY`
     - **Value**: Your OpenAI API key (starts with `sk-...`)
   
   - **Name**: `MONGODB_URI`
     - **Value**: Your MongoDB connection string (e.g., `mongodb+srv://...`)

3. Make sure to add them for **Production**, **Preview**, and **Development** environments

### 3. Deploy

1. After setting environment variables, click **"Deploy"**
2. Vercel will:
   - Install dependencies from `requirements.txt`
   - Build the Python serverless function
   - Deploy your application

### 4. Verify Deployment

1. Once deployed, Vercel will provide you with a URL (e.g., `your-project.vercel.app`)
2. Visit the URL to test your application
3. Test:
   - User signup/login
   - PDF upload and RAG chat
   - Web search functionality
   - Admin dashboard (at `/admin`)

## Important Notes

- **Environment Variables**: Must be set in Vercel dashboard, NOT in `.env` file (`.env` is ignored in production)
- **Serverless Functions**: Vercel functions have execution time limits:
  - Free tier: 10 seconds
  - Pro tier: 60 seconds
  - Large PDF processing may hit these limits
- **Static Files**: CSS, JS, and images are automatically served from the `static/` folder
- **Templates**: HTML templates are served from the `templates/` folder

## Troubleshooting

### Build Fails
- Check that all dependencies are in `requirements.txt`
- Verify Python version compatibility (Vercel uses Python 3.9+)

### Environment Variables Not Working
- Ensure variables are set in Vercel dashboard (not just `.env`)
- Redeploy after adding/changing environment variables

### Static Files Not Loading
- Check that files are in the `static/` folder
- Verify the file paths in your HTML templates

### PDF Upload Fails
- Check function execution time limits
- Large PDFs may need optimization or chunking

## File Structure for Vercel

```
project/
├── api/
│   └── index.py          # Vercel serverless function entry point
├── static/               # Static files (CSS, JS)
├── templates/            # HTML templates
├── app.py                # Flask application
├── requirements.txt      # Python dependencies
├── vercel.json          # Vercel configuration
└── .vercelignore        # Files to ignore during deployment
```

## Support

If you encounter issues:
1. Check Vercel deployment logs in the dashboard
2. Verify all environment variables are set correctly
3. Ensure your GitHub repository has all necessary files

