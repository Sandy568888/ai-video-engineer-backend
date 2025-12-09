import os
import uuid
import threading
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_socketio import SocketIO, emit

app = Flask(__name__)

# CRITICAL: CORS Configuration
CORS(app, resources={
    r"/*": {
        "origins": "*",
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"],
        "supports_credentials": True
    }
})

# SocketIO with CORS
socketio = SocketIO(app, 
    cors_allowed_origins="*",
    async_mode='threading',
    logger=True,
    engineio_logger=True,
    ping_timeout=60,
    ping_interval=25
)

# In-memory job tracking
active_jobs = {}

@app.route('/', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'healthy',
        'service': 'AI Video Engineer Backend',
        'version': '1.0.0'
    }), 200

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'healthy'}), 200

def process_video(video_id, script, template, user_id):
    try:
        socketio.emit('video_status', {
            'id': video_id,
            'status': 'processing',
            'message': 'Starting video generation...',
            'progress': 10,
            'userId': user_id
        })
        
        import time
        stages = [
            (20, "Generating script..."),
            (40, "Creating audio..."),
            (60, "Generating presenter video..."),
            (80, "Compositing video..."),
            (95, "Finalizing..."),
        ]
        
        for progress, message in stages:
            time.sleep(2)
            socketio.emit('video_status', {
                'id': video_id,
                'status': 'processing',
                'message': message,
                'progress': progress,
                'userId': user_id
            })
        
        video_url = f"https://example.com/videos/{video_id}.mp4"
        
        socketio.emit('video_status', {
            'id': video_id,
            'status': 'completed',
            'message': 'Video generation complete!',
            'progress': 100,
            'videoUrl': video_url,
            'userId': user_id
        })
        
        active_jobs[video_id] = {
            'status': 'completed',
            'videoUrl': video_url,
            'completedAt': datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        error_message = str(e)
        print(f"❌ Error processing video {video_id}: {error_message}")
        
        socketio.emit('video_status', {
            'id': video_id,
            'status': 'failed',
            'message': f'Error: {error_message}',
            'progress': 0,
            'userId': user_id
        })
        
        active_jobs[video_id] = {
            'status': 'failed',
            'error': error_message,
            'failedAt': datetime.utcnow().isoformat()
        }

@app.route('/generate-video', methods=['POST', 'OPTIONS'])
def generate_video():
    if request.method == 'OPTIONS':
        return '', 204
        
    try:
        data = request.get_json()
        script = data.get('script', '').strip()
        template = data.get('template', 'presenter1')
        user_id = data.get('userId', 'anonymous')
        
        if not script:
            return jsonify({'error': 'Script is required'}), 400
        
        video_id = str(uuid.uuid4())
        
        active_jobs[video_id] = {
            'status': 'started',
            'startedAt': datetime.utcnow().isoformat()
        }
        
        thread = threading.Thread(
            target=process_video,
            args=(video_id, script, template, user_id)
        )
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'id': video_id,
            'status': 'started',
            'message': 'Video generation initiated'
        }), 202
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/video-status/<video_id>', methods=['GET'])
def get_video_status(video_id):
    job = active_jobs.get(video_id)
    if not job:
        return jsonify({'error': 'Video not found'}), 404
    return jsonify(job)

@socketio.on('connect')
def handle_connect():
    print('✅ Client connected')
    emit('video_status', {'message': 'Connected to AI Video Engineer backend'})

@socketio.on('disconnect')
def handle_disconnect():
    print('❌ Client disconnected')

if __name__ == '__main__':
    port = int(os.getenv('PORT', 10000))
    socketio.run(app, host='0.0.0.0', port=port, debug=False, allow_unsafe_werkzeug=True)

# TTS Admin Endpoints
from app import tts_adapter

@app.route('/tts/health', methods=['GET'])
def tts_health():
    """Check TTS providers health status"""
    try:
        health_status = tts_adapter.health_check()
        return jsonify(health_status), 200
    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e)}), 500

@app.route('/admin/set-tts-provider', methods=['POST', 'GET'])
def set_tts_provider():
    """
    Admin endpoint to manually set TTS provider
    GET /admin/set-tts-provider?provider=vibevoice
    POST /admin/set-tts-provider with body: {"provider": "vibevoice"}
    """
    if request.method == 'POST':
        data = request.get_json()
        provider = data.get('provider', '').lower()
    else:
        provider = request.args.get('provider', '').lower()
    
    if not provider:
        return jsonify({'error': 'provider parameter required'}), 400
    
    success = tts_adapter.set_provider(provider)
    
    if success:
        return jsonify({
            'success': True,
            'provider': provider,
            'message': f'TTS provider set to {provider}'
        }), 200
    else:
        return jsonify({
            'success': False,
            'error': 'Invalid provider. Use "vibevoice" or "elevenlabs"'
        }), 400
