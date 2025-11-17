# 🚀 SportSync AI - Deployment Guide

**Last Updated:** 17 November 2025

---

## ⚠️ Important: Vercel vs Streamlit

**Issue:** You tried to deploy on Vercel, but **Streamlit apps don't work on Vercel!**

### Why Vercel Doesn't Work:
- ❌ Vercel is for **serverless functions** and **static sites** (Next.js, React)
- ❌ Streamlit apps are **long-running Python web servers**
- ❌ Vercel has **10-second timeout** for serverless functions
- ❌ Streamlit needs **persistent websocket connections**

### What Works for Streamlit:
- ✅ **Streamlit Cloud** (FREE, easiest, recommended)
- ✅ **Render** (FREE tier available)
- ✅ **Heroku** (paid, but reliable)
- ✅ **Google Cloud Run** (complex but powerful)
- ✅ **AWS/Azure** (enterprise level)

---

## 🎯 Recommended: Deploy to Streamlit Cloud (FREE!)

### **Step 1: Prepare the Repository**

Your GitHub repo is ready! ✅
- Repository: `https://github.com/Hamodisz/SportSync_AI`
- Branch: `main`

### **Step 2: Create requirements.txt**

First, we need to fix your `requirements.txt` file (it only has test dependencies):

```bash
# I'll create the correct one for you below
```

### **Step 3: Deploy to Streamlit Cloud**

1. **Go to:** https://share.streamlit.io/

2. **Sign in with GitHub**

3. **Click "New app"**

4. **Fill in the form:**
   - **Repository:** `Hamodisz/SportSync_AI`
   - **Branch:** `main`
   - **Main file path:** `apps/main.py`

5. **Advanced settings (IMPORTANT!):**
   - Click "Advanced settings"
   - Add your secrets (environment variables):
     ```
     OPENAI_API_KEY = "sk-your-key-here"
     ```

6. **Click "Deploy!"**

7. **Wait 2-3 minutes** for deployment

8. **Your app will be live at:**
   ```
   https://[your-app-name].streamlit.app
   ```

---

## 📦 Step-by-Step: Fix Requirements.txt

Your current `requirements.txt` is missing the actual app dependencies!

**Current (wrong):**
```
pytest==7.4.3
pytest-cov==4.1.0
pytest-mock==3.12.0
python-dotenv==1.0.0
responses==0.24.1
```

**Should be:**
```
# Core Dependencies
streamlit>=1.50.0
openai>=1.54.0
python-dotenv>=1.0.0

# Optional for video generation
moviepy>=1.0.3
gTTS>=2.3.0
pillow>=10.0.0

# Optional for advanced features
fastapi>=0.104.0
uvicorn>=0.24.0
pydantic>=2.4.0

# Development/Testing (optional for deployment)
pytest>=7.4.3
pytest-cov>=4.1.0
pytest-mock>=3.12.0
responses>=0.24.1
```

---

## 🛠️ Let Me Fix This For You

I'll create the correct `requirements.txt` now with all necessary dependencies.

---

## 🌐 Alternative: Deploy to Render (FREE)

If you prefer Render over Streamlit Cloud:

### **Step 1: Create render.yaml**

I'll create this file for you.

### **Step 2: Deploy**

1. Go to: https://render.com/
2. Sign in with GitHub
3. Click "New +" → "Web Service"
4. Connect your `SportSync_AI` repository
5. Render will auto-detect and deploy!

---

## 🔧 Alternative: Deploy to Heroku

**Note:** Heroku is no longer free, but it's very reliable.

### **Step 1: Create Procfile**

```
web: streamlit run apps/main.py --server.port=$PORT --server.address=0.0.0.0
```

### **Step 2: Deploy**

```bash
# Install Heroku CLI
brew install heroku  # Mac
# or download from heroku.com

# Login
heroku login

# Create app
heroku create your-app-name

# Set environment variables
heroku config:set OPENAI_API_KEY=sk-your-key-here

# Deploy
git push heroku main
```

---

## 📊 Deployment Comparison

| Platform | Cost | Ease | Speed | Recommended |
|----------|------|------|-------|-------------|
| **Streamlit Cloud** | FREE | ⭐⭐⭐⭐⭐ | Fast | ✅ YES |
| **Render** | FREE | ⭐⭐⭐⭐ | Medium | ✅ YES |
| **Heroku** | $7/mo | ⭐⭐⭐⭐ | Fast | 🟡 Maybe |
| **Vercel** | N/A | ❌ | N/A | ❌ NO |
| **Google Cloud Run** | Pay-per-use | ⭐⭐ | Fast | 🟡 Advanced |

---

## 🎯 My Recommendation

**Use Streamlit Cloud!**

### Why?
1. ✅ **FREE** forever for public repos
2. ✅ **Super easy** - just click and deploy
3. ✅ **Made for Streamlit** - no configuration needed
4. ✅ **Automatic updates** - push to GitHub, auto-deploys
5. ✅ **Custom domains** - connect your own domain
6. ✅ **Secrets management** - built-in for API keys

### Cons?
- Only works for Streamlit apps (not an issue for us!)
- Public repos only for free tier

---

## 🚨 Common Deployment Issues

### Issue 1: "Module not found"
**Solution:** Make sure `requirements.txt` includes all dependencies
```bash
# Add missing module to requirements.txt
echo "missing-module==1.0.0" >> requirements.txt
git add requirements.txt
git commit -m "Add missing dependency"
git push
```

### Issue 2: "Port already in use"
**Solution:** Streamlit Cloud handles ports automatically. If running locally:
```bash
streamlit run apps/main.py --server.port 8502
```

### Issue 3: "API key not found"
**Solution:** Add secrets in Streamlit Cloud dashboard:
1. Go to app settings
2. Click "Secrets"
3. Add: `OPENAI_API_KEY = "sk-your-key"`

### Issue 4: "App crashes on startup"
**Solution:** Check logs in Streamlit Cloud dashboard
- Usually missing dependencies or syntax errors
- Fix in GitHub, push, auto-redeploys

---

## 📝 Deployment Checklist

### Before Deployment:
- [ ] Fix `requirements.txt` (I'll do this)
- [ ] Test locally: `streamlit run apps/main.py`
- [ ] Ensure all files are pushed to GitHub
- [ ] Have your OpenAI API key ready

### During Deployment:
- [ ] Choose platform (Streamlit Cloud recommended)
- [ ] Connect GitHub repository
- [ ] Set main file path: `apps/main.py`
- [ ] Add API key to secrets
- [ ] Deploy!

### After Deployment:
- [ ] Test the live app
- [ ] Verify all features work
- [ ] Share the link!
- [ ] Monitor usage (if needed)

---

## 🎯 What I'll Do Next

Let me:
1. ✅ Create proper `requirements.txt`
2. ✅ Create `render.yaml` (for Render option)
3. ✅ Create `.streamlit/config.toml` (for Streamlit Cloud)
4. ✅ Create deployment scripts
5. ✅ Push everything to GitHub

Then you can:
1. Go to https://share.streamlit.io/
2. Click "New app"
3. Point to your repo
4. Add API key
5. Deploy! 🚀

---

## 💡 Quick Deploy (Copy-Paste Commands)

**For Streamlit Cloud (Recommended):**
```bash
# Just push your code (already done!)
git push origin main

# Then go to: https://share.streamlit.io/
# Click "New app" and follow the wizard!
```

**For Render:**
```bash
# Push code (already done!)
git push origin main

# Go to: https://render.com/
# Click "New +" → "Web Service"
# Connect GitHub and deploy!
```

---

## ❓ Need Help?

**Common Questions:**

**Q: Can I use Vercel?**
A: No, Vercel doesn't support Streamlit apps. Use Streamlit Cloud instead.

**Q: Is it really free?**
A: Yes! Streamlit Cloud is free for public repos.

**Q: How long does deployment take?**
A: Usually 2-3 minutes for first deploy, then ~30 seconds for updates.

**Q: Can I use custom domain?**
A: Yes! Streamlit Cloud supports custom domains.

**Q: What if I want to keep repo private?**
A: Streamlit Cloud Pro ($20/mo) supports private repos, or use Render/Heroku.

---

## 🚀 Ready to Deploy?

Tell me:
1. **"Deploy to Streamlit Cloud"** - I'll create all needed files and guide you
2. **"Deploy to Render"** - I'll create render.yaml and guide you
3. **"Show me Heroku"** - I'll create Procfile and guide you
4. **"I have questions"** - Ask me anything!

---

**Let's get your app live! 🎯**
