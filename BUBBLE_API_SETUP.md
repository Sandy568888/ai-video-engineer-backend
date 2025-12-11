# Bubble API Connector Setup Guide

## Backend URL
```
https://ai-video-engineer-backend-1.onrender.com
```

## API Endpoints for Bubble

### 1. Generate Video
**Endpoint:** `/generate-video`  
**Method:** POST  
**Headers:**
```
Content-Type: application/json
```

**Body (JSON):**
```json
{
  "script": "Your video script text here",
  "template": "presenter1",
  "userId": "user@example.com"
}
```

**Response:**
```json
{
  "id": "video-id-123",
  "status": "started",
  "message": "Video generation initiated"
}
```

---

### 2. Check Video Status
**Endpoint:** `/video-status/<video_id>`  
**Method:** GET  
**Example:** `/video-status/video-id-123`

**Response (Processing):**
```json
{
  "id": "video-id-123",
  "status": "processing",
  "message": "Generating audio...",
  "progress": 50
}
```

**Response (Complete):**
```json
{
  "id": "video-id-123",
  "status": "completed",
  "message": "Video generation complete!",
  "progress": 100,
  "videoUrl": "https://wasabi.../video.mp4"
}
```

**Response (Failed):**
```json
{
  "id": "video-id-123",
  "status": "failed",
  "message": "Error: ...",
  "error": "Error details"
}
```

---

## Bubble API Connector Configuration

### API Call 1: Generate Video
```
Name: Generate Video
Use as: Action
Data type: JSON

URL: https://ai-video-engineer-backend-1.onrender.com/generate-video
Method: POST
Body type: JSON
Body:
{
  "script": <script>
  "template": <template>
  "userId": <userId>
}
```

### API Call 2: Get Video Status
```
Name: Get Video Status
Use as: Data
Data type: JSON

URL: https://ai-video-engineer-backend-1.onrender.com/video-status/<video_id>
Method: GET
```

---

## Important Notes

❌ **DO NOT USE:** `/api/v1/generate-video`  
✅ **CORRECT:** `/generate-video`

❌ **DO NOT USE:** `/api/v1/video-status/<id>`  
✅ **CORRECT:** `/video-status/<id>`

The backend does NOT use `/api/v1` prefix. Use the endpoints directly as shown above.

---

## Testing in Bubble

1. **Initialize API in Bubble:**
   - Go to Plugins → API Connector
   - Add new API: "AI Video Backend"
   - Base URL: `https://ai-video-engineer-backend-1.onrender.com`

2. **Test Generate Video:**
   - Call: Generate Video
   - Script: "Hello, this is a test video"
   - Template: "presenter1"
   - Save the returned video ID

3. **Test Get Status:**
   - Call: Get Video Status
   - Use the video ID from step 2
   - Poll every 2-3 seconds until status is "completed"

---

## Workflow Example
```
1. User clicks "Generate Video" button
2. Bubble calls /generate-video → Gets video ID
3. Bubble stores video ID in database
4. Bubble starts polling /video-status/<id> every 2 seconds
5. When status = "completed", display video URL to user
```

---

## Available Templates

- `presenter1` - Simple Presenter (default)
- `sidebyside` - Side by Side layout

---

## Support

For issues or questions, contact the developer.
