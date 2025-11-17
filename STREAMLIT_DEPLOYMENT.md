# 🎨 Deploy Admin Interface to Streamlit Cloud

## 📋 Overview

Deploy `app_streamlit.py` (your video generation + admin tools) to Streamlit Cloud as a **separate, private interface** for content creation.

---

## 🚀 Deployment Steps

### **1. Go to Streamlit Cloud**

Visit: https://share.streamlit.io/

### **2. Sign in with GitHub**

Click "Sign in with GitHub" and authorize Streamlit

### **3. Deploy New App**

1. Click **"New app"**
2. Select your repository: **`Hamodisz/SportSync_AI`**
3. Branch: **`main`**
4. Main file path: **`apps/app_streamlit.py`**

### **4. Advanced Settings (Optional)**

**Python version:** 3.11

**Secrets:** Add your OpenAI API key
```toml
OPENAI_API_KEY = "sk-your-key-here"
```

### **5. Deploy!**

Click **"Deploy"**

Your admin interface will be live at:
```
https://sportsync-admin-[your-name].streamlit.app
```

---

## 🎯 What You'll Have

### **Public Interface (Vercel):**
```
https://sport-sync-ai.vercel.app/app.html
```
**For users to get sport recommendations**

### **Admin Interface (Streamlit):**
```
https://sportsync-admin-[your-name].streamlit.app
```
**For YOU to:**
- Generate videos for YouTube
- View analytics
- Test the system
- Manage content

---

## 🎥 Admin Features Available

### **1. Video Generation Studio**
- Input custom scripts
- Generate AI images
- Create voice-overs
- Compose final video
- Export for YouTube

### **2. System Testing**
- Quick diagnose
- View system health
- Test recommendation engine
- Check LLM status

### **3. Analytics (if enabled)**
- User submission stats
- Popular sports
- System performance

---

## ⚙️ Configuration

### **Environment Variables to Set:**

In Streamlit Cloud settings → Secrets:

```toml
OPENAI_API_KEY = "sk-..."

# Optional: if you want to use different models
CHAT_MODEL = "gpt-4"
CHAT_MODEL_FALLBACK = "gpt-3.5-turbo"
```

---

## 📊 Two-Interface Architecture

```
┌─────────────────────────────────────────────┐
│  PUBLIC (Vercel)                            │
│  └─ Users answer questions                  │
│     └─ Get sport recommendations            │
│        ✅ https://sport-sync-ai.vercel.app  │
└─────────────────────────────────────────────┘

┌─────────────────────────────────────────────┐
│  ADMIN (Streamlit)                          │
│  └─ YOU generate content                    │
│     └─ Create videos for YouTube            │
│        🎨 https://sportsync-admin.streamlit │
└─────────────────────────────────────────────┘
```

---

## 🔒 Security

**Streamlit apps are public by default**, but you can:

1. **Option 1:** Keep URL private (don't share it)
2. **Option 2:** Add password protection (Streamlit secrets)
3. **Option 3:** Use Streamlit Teams (paid, private apps)

For now, just keep the URL private - only you know it!

---

## ✅ Deployment Checklist

- [ ] Go to https://share.streamlit.io/
- [ ] Sign in with GitHub
- [ ] Click "New app"
- [ ] Select SportSync_AI repo
- [ ] Set main file: `apps/app_streamlit.py`
- [ ] Add OPENAI_API_KEY to secrets
- [ ] Click Deploy
- [ ] Wait 2-3 minutes
- [ ] Test the interface
- [ ] Save your admin URL

---

## 🎬 Ready to Deploy?

The admin interface is ready to go! Just follow the steps above and you'll have your content creation studio live in minutes.

**Total time:** ~5 minutes

---

**Let's get your admin interface deployed! 🚀**
