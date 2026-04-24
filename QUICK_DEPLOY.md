# 🚀 Quick Deployment Guide

## Fastest Way to Make Your Pitch Visualizer Public

### Option 1: Railway (Recommended - 5 minutes)

1. **Push to GitHub**
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git branch -M main
   git remote add origin https://github.com/yourusername/pitch-visualizer.git
   git push -u origin main
   ```

2. **Deploy on Railway**
   - Go to [railway.app](https://railway.app)
   - Sign up with GitHub
   - Click "New Project" → "Deploy from GitHub repo"
   - Select your `pitch-visualizer` repository
   - Railway will auto-build and deploy

3. **Configure Environment Variables**
   In Railway dashboard → Settings → Variables:
   ```
   GROQ_API_KEY=gsk_your_groq_key_here
   USE_POLLINATIONS=true
   ENCRYPTION_KEY=YourSecretKey123!
   ENCRYPTION_IV=YourInitVector123
   ```

4. **Your App is Live!**
   - Visit: `https://your-app-name.up.railway.app`
   - Railway provides free SSL and custom domain support

### Option 2: Render (Alternative)

1. **Push to GitHub** (same as above)

2. **Deploy on Render**
   - Go to [render.com](https://render.com)
   - Sign up and connect GitHub
   - Click "New" → "Web Service"
   - Select your repository
   - Render auto-detects using `render.yaml`

3. **Add Environment Variables**
   In Render dashboard → Environment:
   ```
   GROQ_API_KEY=gsk_your_groq_key_here
   USE_POLLINATIONS=true
   ```

4. **Your App is Live!**
   - Visit: `https://your-app.onrender.com`

### Option 3: Glitch (Free but Limited)

1. **Go to [glitch.com](https://glitch.com)**
2. **Choose "New Project" → "Import from GitHub"**
3. **Enter your repo URL**
4. **Add environment variables** in `.env` file
5. **Limited to 1000 requests/hour**

## 🎯 Why Not Vercel?

Your Pitch Visualizer needs:
- ✅ **Long-running processes** (30+ seconds for image generation)
- ✅ **File system access** (steganography, image storage)
- ✅ **Heavy dependencies** (spaCy, ML models)
- ✅ **Background processing** (async image generation)

Vercel is designed for:
- ❌ **Static sites** and **API endpoints** only
- ❌ **10-second execution limits**
- ❌ **No persistent storage**
- ❌ **Cold start delays**

## 🔧 Pre-Deployment Checklist

Before deploying, ensure:

1. **API Keys Ready**
   - Groq API key (required)
   - Hugging Face token (optional, if not using Pollinations)

2. **Environment Variables**
   - Create `.env.example` file for documentation
   - Never commit actual `.env` file

3. **Repository Ready**
   - All files committed to Git
   - `.gitignore` excludes sensitive files
   - README.md with deployment instructions

4. **Test Locally**
   ```bash
   python main.py
   # Visit http://localhost:8000
   # Test with a sample narrative
   ```

## 🌐 Custom Domain Setup

### Railway
1. Go to Settings → Domains
2. Add your custom domain
3. Update DNS records as instructed
4. Railway provides free SSL certificate

### Render
1. Go to Settings → Custom Domains
2. Add your domain
3. Update DNS records
4. Render handles SSL automatically

## 📊 Monitoring & Logs

### Railway
- View logs in Railway dashboard
- Monitor resource usage
- Set up alerts for errors

### Render
- Real-time logs in Render dashboard
- Performance metrics
- Error tracking

## 🔒 Security Considerations

1. **API Keys**: Store as environment variables, never in code
2. **Rate Limiting**: Built into the application
3. **HTTPS**: Automatic on all platforms
4. **CORS**: Configured for your domain
5. **Input Validation**: Already implemented

## 💰 Cost Comparison

| Platform | Free Tier | Paid Plans | Best For |
|----------|-----------|------------|----------|
| Railway | $5/month credit | $5-20/month | Easy deployment |
| Render | 750 hours/month | $7-50/month | Reliable hosting |
| DigitalOcean | - | $5-100/month | Production apps |
| Glitch | 1000 requests/hour | $8/month | Quick testing |

## 🚀 Next Steps After Deployment

1. **Test your live app** with sample narratives
2. **Share the URL** with others
3. **Monitor performance** and logs
4. **Set up custom domain** for professional appearance
5. **Consider scaling** if traffic increases

## 🆘 Troubleshooting

**Common Issues:**
- **Build fails**: Check `requirements.txt` and Python version
- **API errors**: Verify environment variables are set correctly
- **Slow loading**: Image generation takes time, this is normal
- **404 errors**: Check routing and static file serving

**Get Help:**
- Railway: [docs.railway.app](https://docs.railway.app)
- Render: [render.com/docs](https://render.com/docs)
- Check your app logs for specific error messages
