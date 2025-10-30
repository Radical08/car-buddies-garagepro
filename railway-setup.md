# Railway Deployment Guide

## Quick Setup:
1. Push code to GitHub
2. Go to railway.app
3. Connect GitHub repository
4. Add environment variables
5. Deploy!

## Required Environment Variables:
- SECRET_KEY
- DATABASE_URL
- GARAGE_NAME
- GARAGE_ADDRESS
- GARAGE_PHONE
- GARAGE_EMAIL

## First Time Setup:
1. Deploy to Railway
2. Run: `railway run flask init-db`
3. Access your app at: `https://your-app.railway.app`
4. Login with: admin / admin123
5. CHANGE DEFAULT PASSWORD!