# 🎬 AI Video Engineer - Backend

Backend API for AI-powered video generation using OpenAI, **VibeVoice (default TTS)**, ElevenLabs (fallback), and HeyGen.

---

## 🚀 Live Deployment

**Backend URL**: https://ai-video-engineer-backend-tm15.onrender.com

**Status**: ✅ Live and Running

**Current Mode**: 🟡 MOCK MODE

**TTS Provider**: 🎙️ VibeVoice (Default) with ElevenLabs Auto-Fallback

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

## 🎙️ TTS System Architecture

### **VibeVoice as Default**
- High-quality neural TTS via WebSocket streaming
- GPU-accelerated inference
- Lower cost than ElevenLabs
- Supports voice profiles, styles, and seeds
- Output format: `.wav` (HeyGen compatible)

### **Automatic ElevenLabs Fallback**
- Activates automatically if VibeVoice fails
- No manual intervention needed
- Seamless transition to backup provider
- All ElevenLabs features preserved

### **Fallback Flow**
```
User Script
    ↓
TTS Adapter
    ↓
Try VibeVoice (with retry: 1-2 attempts)
    ↓
Success? → Use VibeVoice audio
    ↓
Failed? → Auto-fallback to ElevenLabs
    ↓
Success → Continue to HeyGen
```

---

## 🔄 Mock Mode vs Production Mode

| Feature | Mock Mode | Production Mode |
|---------|-----------|-----------------|
| **API Calls** | Simulated | Real AI services |
| **TTS Provider** | Simulated | VibeVoice → ElevenLabs fallback |
| **Video Output** | Mock URL | Real MP4 download |
| **Cost per Video** | $0 | $0.50 - $2.00 |
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

2. **VibeVoice** (AI Voice - Default)
   - Deploy VibeVoice on GPU server (see deployment section)
   - Get WebSocket endpoint URL
   - Cost: ~$0.15 per video (GPU hosting)

3. **ElevenLabs** (AI Voice - Fallback)
   - Sign up: https://elevenlabs.io
   - Subscribe or add credits
   - Get API key: https://elevenlabs.io/app/settings/api-keys
   - Cost: ~$0.30 per video (only when fallback triggered)

4. **HeyGen** (Avatar Video)
   - Sign up: https://app.heygen.com
   - Add credits (min $30)
   - Get API key: https://app.heygen.com/settings/api
   - Cost: ~$1.50 per video

5. **Wasabi** (Video Storage)
   - Sign up: https://wasabi.com
   - Create bucket: `ai-videos`
   - Get access key and secret
   - Cost: ~$0.01 per video

**Total per video**: $0.50 - $2.00 (less with VibeVoice!)

---

### **Step 2: Deploy VibeVoice GPU Service**

#### **Option A: Docker Deployment**
```bash
# Clone VibeVoice repo
git clone https://github.com/your-org/vibevoice
cd vibevoice

# Build Docker image
docker build -t vibevoice:latest .

# Run on GPU server
docker run -d \
  --gpus all \
  -p 8765:8765 \
  -e VIBEVOICE_MODEL=neural-tts-v2 \
  -e VIBEVOICE_GPU_MEMORY=4GB \
  --name vibevoice-server \
  vibevoice:latest
```

#### **Option B: Direct Python Deployment**
```bash
# On GPU server (Ubuntu + NVIDIA GPU)
pip install -r requirements.txt
python vibevoice_server.py --port 8765 --gpu
```

#### **GPU Requirements**
- NVIDIA GPU (4GB+ VRAM)
- CUDA 11.8+
- Ubuntu 20.04+ or similar
- Recommended: AWS g4dn.xlarge or similar

---

### **Step 3: Add Keys to Render**

1. Go to: **https://dashboard.render.com**
2. Login to your account
3. Click your service: **ai-video-engineer-backend-tm15**
4. Click **"Environment"** tab
5. Click **"Add Environment Variable"**
6. Add each of these:

```bash
# Core Settings
MOCK_MODE=False

# OpenAI
OPENAI_API_KEY=sk-proj-YOUR_KEY_HERE
OPENAI_MODEL=gpt-4

# VibeVoice (Default TTS)
TTS_PROVIDER=vibevoice
VIBEVOICE_WS_ENDPOINT=ws://your-gpu-server:8765/tts
VIBEVOICE_STYLE=neutral
VIBEVOICE_SEED=42
VIBEVOICE_PROFILE=default

# ElevenLabs (Fallback TTS)
ELEVENLABS_API_KEY=YOUR_KEY_HERE
ELEVENLABS_VOICE_ID=21m00Tcm4TlvDq8ikWAM

# HeyGen
HEYGEN_API_KEY=YOUR_KEY_HERE
HEYGEN_AVATAR_ID=default

# Wasabi Storage
WASABI_ACCESS_KEY=YOUR_KEY_HERE
WASABI_SECRET_KEY=YOUR_KEY_HERE
WASABI_BUCKET_NAME=ai-videos
WASABI_REGION=us-east-1
WASABI_ENDPOINT=https://s3.wasabisys.com

# TTS Limits
MAX_TTS_INPUT_CHARS=3000
MAX_TTS_AUDIO_DURATION=90

# TTS Timeouts
VIBEVOICE_CONNECTION_TIMEOUT=10
VIBEVOICE_STREAM_TIMEOUT=5
VIBEVOICE_MAX_RETRIES=2

# Caching
TTS_CACHE_ENABLED=True
TTS_CACHE_DIR=/tmp/tts_cache
```

7. Click **"Save Changes"**
8. Backend auto-redeploys (2-3 minutes)

---

### **Step 4: Verify Production Mode**

Test the health endpoint:
```bash
curl https://ai-video-engineer-backend-tm15.onrender.com/health
```

**Look for**: 
```json
{
  "status": "healthy",
  "mock_mode": false,
  "tts_provider": "vibevoice",
  "vibevoice_available": true,
  "elevenlabs_fallback": true
}
```

---

### **Step 5: Check GPU Health**

Monitor your VibeVoice GPU server:
```bash
curl https://ai-video-engineer-backend-tm15.onrender.com/tts/gpu-health
```

**Expected response**:
```json
{
  "gpu_memory_used_mb": 2048,
  "gpu_load_percent": 45,
  "gpu_temperature_c": 62,
  "active_streams": 2,
  "queue_depth": 0,
  "status": "healthy"
}
```

---

### **Step 6: Generate First Real Video**

```bash
curl -X POST https://ai-video-engineer-backend-tm15.onrender.com/generate-video \
-H "Content-Type: application/json" \
-d '{
  "script": "Welcome! This is my first real AI video using VibeVoice.",
  "template": "presenter1",
  "userId": "your@email.com"
}'
```

Copy the video ID, then check status:
```bash
curl https://ai-video-engineer-backend-tm15.onrender.com/video-status/VIDEO_ID
```

Wait 2-5 minutes. When complete, you'll get a **real downloadable video URL**!

---

## 🎛️ Admin Controls

### **Manual TTS Provider Override**

Switch TTS provider manually (admin only):

```bash
# Force use VibeVoice
curl -X POST https://ai-video-engineer-backend-tm15.onrender.com/admin/set-tts-provider?provider=vibevoice

# Force use ElevenLabs
curl -X POST https://ai-video-engineer-backend-tm15.onrender.com/admin/set-tts-provider?provider=elevenlabs
```

**Note**: This overrides the default but automatic fallback still works!

---

## 📡 API Endpoints

### Core Endpoints

**Health Check**
```bash
GET /health
```

**Generate Video**
```bash
POST /generate-video
{
  "script": "Your video script",
  "template": "presenter1",
  "userId": "user@example.com"
}
```

**Check Video Status**
```bash
GET /video-status/{video_id}
```

**List All Jobs**
```bash
GET /jobs
GET /jobs?userId=user@example.com
```

### TTS Management Endpoints

**GPU Health Monitor**
```bash
GET /tts/gpu-health
```

**Set TTS Provider (Admin)**
```bash
POST /admin/set-tts-provider?provider=vibevoice
POST /admin/set-tts-provider?provider=elevenlabs
```

**TTS Analytics**
```bash
GET /tts/analytics
GET /tts/analytics?userId=user@example.com
```

---

## 🧠 Advanced Features

### **1. TTS Output Caching**
- Caches generated audio by text hash
- Reuses audio for identical scripts
- Saves processing time and costs
- Cache location: `/tmp/tts_cache/`
- Auto-cleanup after 7 days

### **2. Automatic Retry Logic**
- VibeVoice: 1-2 retry attempts
- Connection timeout: 10 seconds
- Stream timeout: 5 seconds idle
- Auto-fallback after retries exhausted

### **3. Input & Output Limits**
- Max script length: 3000 characters
- Max audio duration: 90 seconds
- Early rejection of oversized requests
- Prevents GPU overload

### **4. Structured JSON Logging**
All TTS operations logged:
```json
{
  "provider": "vibevoice",
  "fallback_used": false,
  "execution_ms": 2130,
  "audio_duration_s": 45,
  "video_id": "xyz123",
  "user_id": "user@example.com",
  "status": "success",
  "timestamp": "2025-01-12T10:30:00Z"
}
```

### **5. Multi-Language Provider Routing**
- Auto-detects input language
- English → VibeVoice (default)
- Other languages → ElevenLabs fallback
- Seamless language support

### **6. Voice Consistency Parameters**
Control voice output:
```bash
VIBEVOICE_STYLE=neutral|excited|calm
VIBEVOICE_SEED=42  # reproducible output
VIBEVOICE_PROFILE=default|professional|casual
```

---

## 🧹 Maintenance & Cleanup

### **Automatic Wasabi Cleanup**

Run cleanup script to save storage costs:
```bash
# Delete old audio files (7+ days)
python scripts/cleanup_wasabi.py --audio --days 7

# Delete old video files (30+ days)
python scripts/cleanup_wasabi.py --videos --days 30

# Dry run (preview deletions)
python scripts/cleanup_wasabi.py --audio --days 7 --dry-run
```

**Recommended**: Set up cron job
```bash
# Add to crontab (runs daily at 2 AM)
0 2 * * * cd /path/to/backend && python scripts/cleanup_wasabi.py --audio --days 7 --videos --days 30
```

---

## 🔧 Tech Stack

- **Framework**: Flask 3.1.2
- **Server**: Gunicorn 23.0.0 (gthread)
- **CORS**: Flask-CORS 6.0.1
- **AI Services**: 
  - OpenAI (script enhancement)
  - VibeVoice (default TTS)
  - ElevenLabs (fallback TTS)
  - HeyGen (avatar video)
- **Storage**: Boto3 + Wasabi S3
- **Caching**: File-based TTS cache
- **Logging**: Structured JSON logs
- **Deployment**: Render.com
- **Python**: 3.13

---

## 💰 Cost Summary

### Mock Mode (Current)
- **Hosting**: Free (Render free tier)
- **Per Video**: $0
- **Total**: $0/month

### Production Mode with VibeVoice
- **Hosting**: Free or $7/month (Render Pro for always-on)
- **GPU Server**: $0.50/hour (AWS g4dn.xlarge) = ~$360/month
- **Per Video**: $0.50 - $2.00
  - OpenAI: ~$0.10
  - VibeVoice: ~$0.15 (GPU cost per minute)
  - HeyGen: ~$1.50
  - Wasabi: ~$0.01
- **Fallback Cost**: +$0.30 when ElevenLabs used

### Cost Optimization Tips
- Use TTS caching to reduce duplicate generations
- Auto-cleanup old files to minimize storage
- Monitor GPU health to optimize utilization
- Use canary rollout to control VibeVoice usage

---

## 🛠️ Local Development

```bash
git clone https://github.com/Sandy5688/ai-video-engineer-backend.git
cd ai-video-engineer-backend

pip install -r requirements.txt

cp .env.example .env
# Edit .env with your settings

python app/main.py
```

Runs on: http://localhost:5000

---

## 🧪 Testing

### **Smoke Tests**

Test VibeVoice integration:
```bash
pytest tests/test_tts_adapter.py -v
```

Test automatic fallback:
```bash
pytest tests/test_tts_fallback.py -v
```

Test full video pipeline:
```bash
pytest tests/test_video_generation.py -v
```

### **Manual Testing**

1. Test VibeVoice TTS only:
```bash
curl -X POST http://localhost:5000/test/tts \
-H "Content-Type: application/json" \
-d '{"text": "Hello world", "provider": "vibevoice"}'
```

2. Test ElevenLabs fallback:
```bash
curl -X POST http://localhost:5000/test/tts \
-H "Content-Type: application/json" \
-d '{"text": "Hello world", "provider": "elevenlabs"}'
```

---

## 🚀 Deployment Strategy

### **Canary Rollout Plan**

**Phase 1: 5% Traffic**
- Route 5% of requests to VibeVoice
- Monitor success rate, latency, quality
- Duration: 1 week

**Phase 2: 25% Traffic**
- Increase to 25% if Phase 1 successful
- Monitor GPU utilization
- Duration: 1 week

**Phase 3: 100% Traffic**
- Full rollout with ElevenLabs fallback
- Monitor costs and quality
- Keep fallback always active

### **Rollback Plan**

**Instant Rollback** (if critical issues):
```bash
# In Render dashboard, set:
TTS_PROVIDER=elevenlabs
```
Redeploys in ~2 minutes, all traffic to ElevenLabs.

**Gradual Rollback** (if quality concerns):
```bash
# Reduce VibeVoice traffic percentage
# Keep monitoring both providers
```

---

## 🆘 Troubleshooting

### Backend Sleeping (Free Tier)
**Issue**: First request takes 30-60 seconds

**Solution**: 
- Wait for backend to wake up
- OR upgrade to Render Pro ($7/month)

### VibeVoice Connection Errors
**Issue**: TTS fails with connection timeout

**Solution**:
- Check GPU server is running
- Verify `VIBEVOICE_WS_ENDPOINT` is correct
- Check GPU server logs
- Automatic fallback to ElevenLabs will activate

### GPU Out of Memory
**Issue**: GPU crashes or rejects requests

**Solution**:
- Check GPU health endpoint
- Reduce concurrent requests
- Increase GPU server resources
- Clear TTS cache if needed

### ElevenLabs Fallback Triggered Too Often
**Issue**: High fallback rate indicates VibeVoice issues

**Solution**:
- Check GPU health metrics
- Review VibeVoice server logs
- Verify network connectivity
- Consider GPU server upgrade

### TTS Cache Issues
**Issue**: Stale or corrupted cached audio

**Solution**:
```bash
# Clear TTS cache
rm -rf /tmp/tts_cache/*

# Or disable caching temporarily
TTS_CACHE_ENABLED=False
```

### API Key Errors
**Issue**: Videos fail in production

**Solution**:
- Verify all keys are correct
- Check credits/quotas in dashboards
- Review Render logs for errors
- Test individual services separately

### CORS Errors
**Issue**: Frontend can't connect

**Solution**:
- Already configured
- Check Render logs if issues persist
- Verify frontend domain is whitelisted

---

## 📊 Monitoring

### Check Backend Health
```bash
curl https://ai-video-engineer-backend-tm15.onrender.com/health
```

### Monitor GPU Server
```bash
curl https://ai-video-engineer-backend-tm15.onrender.com/tts/gpu-health
```

### View Active Jobs
```bash
curl https://ai-video-engineer-backend-tm15.onrender.com/jobs
```

### TTS Analytics Dashboard
```bash
curl https://ai-video-engineer-backend-tm15.onrender.com/tts/analytics
```

### Monitor Costs
- OpenAI: https://platform.openai.com/usage
- ElevenLabs: Dashboard
- HeyGen: Dashboard
- Wasabi: Billing section
- Render: https://dashboard.render.com
- GPU Server: AWS/GCP/Azure billing

---

## 📁 Project Structure

```
ai-video-engineer-backend/
├── app/
│   ├── main.py                 # Flask app entry point
│   ├── tts_adapter.py          # TTS provider abstraction
│   ├── vibevoice_client.py     # VibeVoice WebSocket client
│   ├── elevenlabs_client.py    # ElevenLabs API client
│   ├── routes/
│   │   ├── video.py            # Video generation routes
│   │   ├── tts.py              # TTS management routes
│   │   └── admin.py            # Admin control routes
│   ├── services/
│   │   ├── openai_service.py   # Script enhancement
│   │   ├── heygen_service.py   # Video generation
│   │   └── storage_service.py  # Wasabi S3 operations
│   └── utils/
│       ├── cache.py            # TTS caching logic
│       ├── logger.py           # Structured JSON logging
│       └── validators.py       # Input validation
├── scripts/
│   └── cleanup_wasabi.py       # Storage cleanup automation
├── tests/
│   ├── test_tts_adapter.py
│   ├── test_vibevoice.py
│   ├── test_fallback.py
│   └── test_video_generation.py
├── requirements.txt
├── .env.example
├── Dockerfile
└── README.md
```

---

## 🔒 Security

- ✅ API keys in Render environment (encrypted)
- ✅ Never committed to GitHub
- ✅ CORS configured
- ✅ HTTPS enforced
- ✅ Input validation on all endpoints
- ✅ Rate limiting on TTS endpoints
- ✅ Admin routes protected
- ✅ GPU server behind firewall (recommended)

---

## 🔮 Future Roadmap

### **Phase 1: Job Queue System** (Q2 2025)
- Replace threading with Redis + Celery
- Support retries, concurrency limits, delayed jobs
- Durable job state across restarts

### **Phase 2: Internal Video Engine** (Q3 2025)
- Replace HeyGen to eliminate per-video costs
- Template-based video compositing
- Full control over rendering pipeline

### **Phase 3: Real-Time Lip-Sync** (Q4 2025)
- Multi-language dubbing support
- Advanced lip-sync alignment
- Real-time presenter rendering

### **Phase 4: GPU Autoscaling** (2026)
- Kubernetes/Docker Swarm support
- Multi-GPU load balancing
- Auto-scale based on demand

---

## 📄 License

Proprietary - All rights reserved

---

## 📞 Support

- Render docs: https://render.com/docs
- Check logs for errors
- Test health endpoint
- Review GPU health metrics
- Check TTS analytics dashboard

---

## 🎯 Quick Reference

**Backend URL**: https://ai-video-engineer-backend-tm15.onrender.com

**Key Endpoints**:
- Health: `/health`
- Generate: `/generate-video`
- Status: `/video-status/{id}`
- GPU: `/tts/gpu-health`
- Admin: `/admin/set-tts-provider`

**Default TTS**: VibeVoice (with ElevenLabs auto-fallback)

**Status**: ✅ Production Ready  
**Current Mode**: 🟡 Mock  
**TTS Provider**: 🎙️ VibeVoice → ElevenLabs  
**Updated**: January 2026

---

**Ready to go live with VibeVoice? Follow the deployment guide above!** 🚀
