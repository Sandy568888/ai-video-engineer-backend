# VibeVoice TTS Integration Runbook

## Overview
This backend now uses **VibeVoice as the default TTS provider** with **automatic ElevenLabs fallback**.

## Architecture
```
Video Generation Request
    ↓
TTS Adapter (app/tts_adapter.py)
    ↓
Try VibeVoice (WebSocket) → If fails → ElevenLabs (API)
    ↓
Audio File (.wav)
    ↓
Upload to Wasabi
    ↓
HeyGen Avatar Video
    ↓
Final Video
```

## Environment Variables

### Required for VibeVoice
```bash
VIBEVOICE_WS_ENDPOINT=wss://your-vibevoice-server.com/ws
VIBEVOICE_VOICE_ID=default
VIBEVOICE_SAMPLE_RATE=24000
TTS_PROVIDER=vibevoice  # default
```

### Required for ElevenLabs (Fallback)
```bash
ELEVENLABS_API_KEY=your_api_key
ELEVENLABS_VOICE_ID=your_voice_id
```

### Other Settings
```bash
MOCK_MODE=False  # Set to True for testing without real services
```

## Deployment

### 1. Deploy VibeVoice Service on GPU

**Option A: Using Docker**
```bash
# Build and run VibeVoice
./scripts/deploy_vibevoice.sh

# Check logs
docker logs -f vibevoice-tts

# Stop service
docker stop vibevoice-tts
```

**Option B: Manual Deployment**
```bash
# Install dependencies
pip install -r vibevoice_requirements.txt

# Run server
python scripts/vibevoice_server.py

# Server will listen on ws://0.0.0.0:8765
```

### 2. Update Backend Environment
```bash
# Set VibeVoice endpoint
export VIBEVOICE_WS_ENDPOINT=wss://your-gpu-server.com:8765

# Verify connection
curl http://localhost:10000/tts/health
```

### 3. Deploy Backend
```bash
# Install dependencies
pip install -r requirements.txt

# Run backend
python app.py
```

## API Endpoints

### Check TTS Health
```bash
GET /tts/health

Response:
{
  "current_provider": "vibevoice",
  "providers": {
    "vibevoice": {
      "status": "configured",
      "endpoint": "wss://..."
    },
    "elevenlabs": {
      "status": "configured",
      "mock_mode": false
    }
  }
}
```

### Manually Switch Provider (Admin Only)
```bash
# Switch to ElevenLabs
GET /admin/set-tts-provider?provider=elevenlabs

# Switch to VibeVoice
GET /admin/set-tts-provider?provider=vibevoice

# Or use POST
POST /admin/set-tts-provider
Body: {"provider": "vibevoice"}
```

## Testing

### Test TTS Adapter
```bash
python scripts/test_tts.py
```

### Test Video Generation
```bash
curl -X POST http://localhost:10000/generate-video \
  -H "Content-Type: application/json" \
  -d '{
    "script": "Hello world, this is a test video.",
    "template": "presenter1",
    "userId": "test-user"
  }'
```

### Check Video Status
```bash
curl http://localhost:10000/video-status/<video_id>
```

## How Fallback Works

The fallback is **AUTOMATIC** and happens inside `tts_adapter.generate_audio()`:

1. **Try VibeVoice first** (if `TTS_PROVIDER=vibevoice`)
2. **If VibeVoice fails** (connection error, timeout, or returns None):
   - Log the error
   - Automatically switch to ElevenLabs
3. **Use ElevenLabs** as backup
4. **If both fail**: Return None and raise error

**No manual intervention needed** - fallback is built into the code.

## Canary Rollout Plan

### Phase 1: Staging (Week 1)
- Deploy VibeVoice on staging GPU
- Set `TTS_PROVIDER=vibevoice` on staging
- Test with 100% staging traffic
- Monitor logs for fallback events

### Phase 2: 5% Production (Week 2)
- Deploy VibeVoice on production GPU
- Route 5% of traffic to new backend with VibeVoice
- Monitor metrics:
  - TTS success rate
  - Fallback frequency
  - Audio quality
  - Latency

### Phase 3: 25% Production (Week 3)
- If Phase 2 successful, increase to 25%
- Continue monitoring

### Phase 4: 100% Production (Week 4)
- Full rollout if all metrics good
- ElevenLabs remains as fallback

## Monitoring

### Key Metrics
- **TTS Success Rate**: % of audio generations that succeed
- **Fallback Rate**: % using ElevenLabs fallback
- **Average Latency**: Time to generate audio
- **Error Rate**: Failed generations (both providers failed)

### Logs to Watch
```bash
# VibeVoice attempts
"Attempting audio generation with VibeVoice (primary)"

# VibeVoice success
"✅ VibeVoice succeeded: audio_xyz.wav"

# Fallback triggered
"❌ VibeVoice failed with error"
"🔄 Falling back to ElevenLabs..."

# ElevenLabs used
"✅ ElevenLabs succeeded: audio_xyz.mp3"

# Complete failure
"❌ ElevenLabs also failed (returned None)"
```

## Rollback Plan

### Instant Rollback (Manual Override)
```bash
# Force ElevenLabs as primary provider
curl -X POST http://localhost:10000/admin/set-tts-provider \
  -d '{"provider": "elevenlabs"}'
```

### Full Rollback (Environment Variable)
```bash
# Update environment
export TTS_PROVIDER=elevenlabs

# Restart backend
# All new requests will use ElevenLabs directly
```

### Emergency Rollback (Code Level)
If needed, temporarily comment out VibeVoice in `app/tts_adapter.py`:
```python
# Force ElevenLabs only
# if _current_provider == 'vibevoice':
#     ... VibeVoice code ...

# Jump directly to ElevenLabs
elevenlabs = ElevenLabsService()
...
```

## Troubleshooting

### VibeVoice Connection Fails
```bash
# Check endpoint is reachable
curl -v wss://your-vibevoice-server.com/ws

# Check environment variable
echo $VIBEVOICE_WS_ENDPOINT

# Check logs
tail -f app.log | grep VibeVoice
```

### Audio Format Issues
VibeVoice outputs `.wav` files (HeyGen compatible).
If HeyGen rejects audio, check:
- Sample rate (should be 24000 Hz)
- Format (mono, 16-bit PCM)
- File isn't corrupted

### High Fallback Rate
If >20% requests fall back to ElevenLabs:
1. Check VibeVoice server health
2. Check network latency
3. Scale VibeVoice GPU resources
4. Review VibeVoice logs for errors

## Support

### VibeVoice Issues
- Check VibeVoice service logs
- Verify GPU availability
- Contact VibeVoice support if API issues

### ElevenLabs Issues
- Check API key validity
- Verify rate limits not exceeded
- Check ElevenLabs status page

### Backend Issues
- Check `/tts/health` endpoint
- Review application logs
- Test with `scripts/test_tts.py`

## Files Changed
- `app/tts_adapter.py` - Main TTS adapter with fallback logic
- `app/services/vibevoice_service.py` - VibeVoice WebSocket client
- `app/services/elevenlabs_service.py` - ElevenLabs service (unchanged)
- `app.py` - Updated video generation to use TTS adapter
- `requirements.txt` - Added websockets dependency
- `Dockerfile.vibevoice` - VibeVoice GPU deployment
- `scripts/vibevoice_server.py` - VibeVoice WebSocket server
- `scripts/test_tts.py` - TTS testing script

## Next Steps
1. ✅ Code integrated
2. ⏳ Deploy VibeVoice to staging GPU
3. ⏳ Test full pipeline (TTS → HeyGen → Wasabi)
4. ⏳ Canary rollout to production
5. ⏳ Monitor and optimize

---
**Last Updated**: December 9, 2024
**Version**: 1.0.0
