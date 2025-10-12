# 🎬 AI Video Engineer - Backend

Backend API for AI-powered video generation using OpenAI, ElevenLabs, and HeyGen.

---

## 🚀 Live Deployment

**Backend URL**: https://ai-video-engineer-backend-tm15.onrender.com

**Status**: ✅ Live and Running

**Current Mode**: 🟡 MOCK MODE

---

## 🎯 What is Mock Mode?

**Mock Mode** means:
- ✅ All API endpoints work perfectly
- ✅ Video generation is **simulated** (no real AI calls)
- ✅ Progress updates in real-time
- ✅ Mock video URLs generated
- ✅ **Zero API costs** - completely free
- ✅ Perfect for testing and demos

---

## 🔄 Mock Mode vs Production Mode

| Feature | Mock Mode | Production Mode |
|---------|-----------|-----------------|
| **API Calls** | Simulated | Real AI services |
| **Video Output** | Mock URL | Real MP4 download |
| **Cost per Video** | $0 | $0.70 - $2.50 |
| **Processing Time** | ~20 seconds | 2-5 minutes |
| **API Keys** | Not needed | Required |

---

## 🚀 How to Switch to PRODUCTION MODE

### **Step 1: Get API Keys**

You need accounts and API keys from these services:

1. **OpenAI** (Script Enhancement)
   - Sign up: https://platform.openai.com
   - Add payment method
   - Get API key: https://platform.openai.com/api-keys
   - Cost: ~$0.10 per video

2. **ElevenLabs** (AI Voice)
   - Sign up: https://elevenlabs.io
   - Subscribe or add credits
   - Get API key: https://elevenlabs.io/app/settings/api-keys
   - Cost: ~$0.30 per video

3. **HeyGen** (Avatar Video)
   - Sign up: https://app.heygen.com
   - Add credits (min $30)
   - Get API key: https://app.heygen.com/settings/api
   - Cost: ~$1.50 per video

4. **Wasabi** (Video Storage)
   - Sign up: https://wasabi.com
   - Create bucket: `ai-videos`
   - Get access key and secret
   - Cost: ~$0.01 per video

**Total per video**: $0.70 - $2.50

---

### **Step 2: Add Keys to Render**

1. Go to: **https://dashboard.render.com**
2. Login to your account
3. Click your service: **ai-video-engineer-backend-tm15**
4. Click **"Environment"** tab
5. Click **"Add Environment Variable"**
6. Add each of these:MOCK_MODE=FalseOPENAI_API_KEY=sk-proj-YOUR_KEY_HERE
OPENAI_MODEL=gpt-4ELEVENLABS_API_KEY=YOUR_KEY_HERE
ELEVENLABS_VOICE_ID=21m00Tcm4TlvDq8ikWAMHEYGEN_API_KEY=YOUR_KEY_HERE
HEYGEN_AVATAR_ID=defaultWASABI_ACCESS_KEY=YOUR_KEY_HERE
WASABI_SECRET_KEY=YOUR_KEY_HERE
WASABI_BUCKET_NAME=ai-videos
WASABI_REGION=us-east-1
WASABI_ENDPOINT=https://s3.wasabisys.com

7. Click **"Save Changes"**
8. Backend auto-redeploys (2-3 minutes)

---

### **Step 3: Verify Production Mode**

Test the health endpoint:
```bashcurl https://ai-video-engineer-backend-tm15.onrender.com/health

**Look for**: `"mock_mode": false`

---

### **Step 4: Generate First Real Video**
```bashcurl -X POST https://ai-video-engineer-backend-tm15.onrender.com/generate-video 
-H "Content-Type: application/json" 
-d '{
"script": "Welcome! This is my first real AI video.",
"template": "presenter1",
"userId": "your@email.com"
}'

Copy the video ID, then check status:
```bashcurl https://ai-video-engineer-backend-tm15.onrender.com/video-status/VIDEO_ID

Wait 2-5 minutes. When complete, you'll get a **real downloadable video URL**!

---

## ⚠️ Important Notes

### **Costs**
- Each video: $0.70 - $2.50
- Monitor usage in service dashboards
- Set budget alerts

### **Processing Time**
- Mock: ~20 seconds
- Production: 2-5 minutes

### **Switch Back to Mock**
1. Go to Render → Environment
2. Set `MOCK_MODE=True`
3. Save changes

---

## 📡 API Endpoints

### Health CheckGET /health

### Generate VideoPOST /generate-video{
"script": "Your video script",
"template": "presenter1",
"userId": "user@example.com"
}

### Check Video StatusGET /video-status/{video_id}

### List All JobsGET /jobs
GET /jobs?userId=user@example.com

---

## 🔧 Tech Stack

- **Framework**: Flask 3.1.2
- **Server**: Gunicorn 23.0.0 (gthread)
- **CORS**: Flask-CORS 6.0.1
- **AI Services**: OpenAI, ElevenLabs, HeyGen
- **Storage**: Boto3 + Wasabi S3
- **Deployment**: Render.com
- **Python**: 3.13

---

## 💰 Cost Summary

### Mock Mode (Current)
- **Hosting**: Free (Render free tier)
- **Per Video**: $0
- **Total**: $0/month

### Production Mode
- **Hosting**: Free or $7/month (Render Pro for always-on)
- **Per Video**: $0.70 - $2.50
- **Monthly**: Depends on usage

---

## 🛠️ Local Development
```bashgit clone https://github.com/Sandy5688/ai-video-engineer-backend.git
cd ai-video-engineer-backendpip install -r requirements.txtcp .env.example .env
Edit .env with your settingspython app/main.py

Runs on: http://localhost:5000

---

## 🆘 Troubleshooting

### Backend Sleeping (Free Tier)
**Issue**: First request takes 30-60 seconds

**Solution**: 
- Wait for backend to wake up
- OR upgrade to Render Pro ($7/month)

### API Key Errors
**Issue**: Videos fail in production

**Solution**:
- Verify all keys are correct
- Check credits/quotas in dashboards
- Review Render logs for errors

### CORS Errors
**Issue**: Frontend can't connect

**Solution**:
- Already configured
- Check Render logs if issues persist

---

## 📊 Monitoring

### Check Backend Health
```bashcurl https://ai-video-engineer-backend-tm15.onrender.com/health

### View Active Jobs
```bashcurl https://ai-video-engineer-backend-tm15.onrender.com/jobs

### Monitor Costs
- OpenAI: https://platform.openai.com/usage
- ElevenLabs: Dashboard
- HeyGen: Dashboard
- Wasabi: Billing section
- Render: https://dashboard.render.com

---

## 🔒 Security

- ✅ API keys in Render environment (encrypted)
- ✅ Never committed to GitHub
- ✅ CORS configured
- ✅ HTTPS enforced

---

## 📄 License

Proprietary - All rights reserved

---

## 📞 Support

- Render docs: https://render.com/docs
- Check logs for errors
- Test health endpoint

---

**Status**: ✅ Production Ready  
**Current Mode**: 🟡 Mock  
**Updated**: October 2025

---

**Ready to go live? Follow the guide above to switch to production!** 🚀
