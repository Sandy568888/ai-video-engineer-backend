# AI Video Engineer - Backend

AI-powered video generation backend built with Flask, OpenAI, ElevenLabs, and HeyGen.

## 🚀 Features

- ✅ Script polishing with GPT-4
- ✅ AI voiceover generation with ElevenLabs
- ✅ Avatar video creation with HeyGen
- ✅ Video storage on Wasabi S3
- ✅ Real-time progress tracking
- ✅ Mock mode for testing without API credits

## 🎯 Current Setup: Mock Mode

No API calls are made. Perfect for testing and demos.

## 💰 Estimated Costs (Production Mode)

Per video: ~$0.70 - $2.50

See full documentation in .env.example file.

## 📡 API Endpoints

- GET /health
- POST /generate-video
- GET /video-status/{id}
- GET /jobs

## �� Deployment

Backend URL: https://ai-video-engineer-backend-tm15.onrender.com

Status: MOCK MODE (Switch to production when API keys are available)
