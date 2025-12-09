#!/bin/bash
# Deploy VibeVoice to GPU environment

echo "🚀 Deploying VibeVoice TTS Service..."

# Build Docker image
docker build -f Dockerfile.vibevoice -t vibevoice-tts:latest .

# Run container with GPU support
docker run -d \
  --name vibevoice-tts \
  --gpus all \
  -p 8765:8765 \
  --restart unless-stopped \
  vibevoice-tts:latest

echo "✅ VibeVoice deployed on port 8765"
echo "WebSocket endpoint: ws://localhost:8765"
