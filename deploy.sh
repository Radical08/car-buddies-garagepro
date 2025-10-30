#!/bin/bash
echo "🚀 Deploying Car Buddies GaragePro to Railway..."

# Initialize database on Railway
railway run flask init-db

echo "✅ Deployment complete!"
echo "🌐 Your app is live at: https://your-app.railway.app"
echo "👤 Login with: admin / admin123"
echo "⚠️  Remember to change default credentials!"