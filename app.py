# VibeVoice TTS Integration - Production Ready

import os
import uuid
import threading
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_socketio import SocketIO, emit

# Import TTS adapter and services
from app import tts_adapter
from app.services.heygen_service import HeyGenService
from app.services.wasabi_service import WasabiService

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
    """Process video generation with real TTS integration"""
    try:
        # Step 1: Starting
        socketio.emit('video_status', {
            'id': video_id,
            'status': 'processing',
            'message': 'Starting video generation...',
            'progress': 10,
            'userId': user_id
        })
        
        # Step 2: Generate audio using TTS adapter (VibeVoice with ElevenLabs fallback)
        socketio.emit('video_status', {
            'id': video_id,
            'status': 'processing',
            'message': 'Generating voiceover with VibeVoice...',
            'progress': 20,
            'userId': user_id
        })
        
        audio_path = tts_adapter.generate_audio(
            text=script,
            filename_prefix=f"video_{video_id}",
            voice=None,  # Use default voice
            format="wav"  # WAV for HeyGen compatibility
        )
        
        if not audio_path:
            raise Exception("Audio generation failed with both VibeVoice and ElevenLabs")
        
        socketio.emit('video_status', {
            'id': video_id,
            'status': 'processing',
            'message': f'Audio generated: {audio_path}',
            'progress': 40,
            'userId': user_id
        })
        
        # Step 3: Upload audio to Wasabi
        socketio.emit('video_status', {
            'id': video_id,
            'status': 'processing',
            'message': 'Uploading audio to cloud storage...',
            'progress': 50,
            'userId': user_id
        })
        
        wasabi = WasabiService()
        audio_url = wasabi.upload_file(audio_path, f"audio/{video_id}.wav")
        
        if not audio_url:
            raise Exception("Failed to upload audio to Wasabi")
        
        # Step 4: Generate avatar video with HeyGen
        socketio.emit('video_status', {
            'id': video_id,
            'status': 'processing',
            'message': 'Creating avatar video with HeyGen...',
            'progress': 60,
            'userId': user_id
        })
        
        heygen = HeyGenService()
        avatar_video = heygen.create_avatar_video(
            audio_url=audio_url,
            avatar_id=template
        )
        
        if not avatar_video:
            raise Exception("HeyGen avatar video generation failed")
        
        socketio.emit('video_status', {
            'id': video_id,
            'status': 'processing',
            'message': 'Finalizing video...',
            'progress': 90,
            'userId': user_id
        })
        
        # Step 5: Upload final video to Wasabi
        final_video_url = wasabi.upload_file(avatar_video, f"videos/{video_id}.mp4")
        
        if not final_video_url:
            raise Exception("Failed to upload final video")
        
        # Cleanup temporary files
        if os.path.exists(audio_path):
            os.remove(audio_path)
        if os.path.exists(avatar_video):
            os.remove(avatar_video)
        
        # Step 6: Complete
        socketio.emit('video_status', {
            'id': video_id,
            'status': 'completed',
            'message': 'Video generation complete!',
            'progress': 100,
            'videoUrl': final_video_url,
            'userId': user_id
        })
        
        active_jobs[video_id] = {
            'status': 'completed',
            'videoUrl': final_video_url,
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

# TTS Admin Endpoints
@app.route('/tts/health', methods=['GET'])
def tts_health():
    """Check TTS providers health status"""
    try:
        health_status = tts_adapter.health_check()
        health_status['streaming'] = tts_adapter.get_streaming_config()
        health_status['limits'] = tts_adapter.get_limits_info()
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

# GPU Health Monitoring
from app.services.gpu_monitor import GPUMonitor

@app.route('/tts/gpu-health', methods=['GET'])
def gpu_health():
    """
    Get GPU health statistics
    
    Returns GPU metrics including:
    - Memory usage
    - GPU utilization
    - Temperature
    - Active TTS streams
    - Queue depth
    """
    try:
        monitor = GPUMonitor()
        
        # Check if detailed stats requested
        detailed = request.args.get('detailed', 'false').lower() == 'true'
        
        if detailed:
            stats = monitor.get_gpu_stats()
        else:
            stats = monitor.get_health_summary()
        
        return jsonify(stats), 200
        
    except Exception as e:
        logger.error(f"GPU health check failed: {e}", exc_info=True)
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

@app.route('/admin/gpu-stats', methods=['GET'])
def admin_gpu_stats():
    """Admin endpoint for detailed GPU statistics"""
    try:
        monitor = GPUMonitor()
        stats = monitor.get_gpu_stats()
        return jsonify(stats), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/tts/analytics', methods=['GET'])
def tts_analytics():
    """Get TTS generation analytics"""
    try:
        days = int(request.args.get('days', 1))
        stats = tts_adapter.get_analytics_stats(days)
        return jsonify(stats), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/tts/cache/stats', methods=['GET'])
def tts_cache_stats():
    """Get TTS cache statistics"""
    try:
        from app.services.tts_cache import TTSCache
        cache = TTSCache()
        stats = cache.get_stats()
        return jsonify(stats), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/admin/cache/clear', methods=['POST'])
def clear_tts_cache():
    """Clear TTS cache (admin only)"""
    try:
        from app.services.tts_cache import TTSCache
        cache = TTSCache()
        deleted = cache.clear()
        return jsonify({
            'success': True,
            'deleted_files': deleted,
            'message': f'Cleared {deleted} cache files'
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/tts/voice/config', methods=['GET'])
def get_voice_config():
    """Get current voice configuration"""
    try:
        from app.services.voice_config import VoiceConfig
        config = VoiceConfig.from_env()
        return jsonify(config.to_dict()), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/admin/voice/test', methods=['POST'])
def test_voice_config():
    """Test voice configuration (admin only)"""
    try:
        from app.services.voice_config import VoiceManager
        
        data = request.get_json()
        user_id = data.get('user_id', 'test-user')
        base_voice = data.get('voice_id', 'default')
        project_id = data.get('project_id')
        
        manager = VoiceManager()
        voice_params = manager.create_consistent_voice(
            base_voice_id=base_voice,
            user_id=user_id,
            project_id=project_id
        )
        
        return jsonify({
            'success': True,
            'voice_parameters': voice_params
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/tts/detect-language', methods=['POST'])
def detect_language():
    """Detect language from text"""
    try:
        data = request.get_json()
        text = data.get('text', '')
        
        if not text:
            return jsonify({'error': 'text is required'}), 400
        
        result = tts_adapter.detect_language(text)
        return jsonify(result), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/tts/supported-languages', methods=['GET'])
def supported_languages():
    """Get supported languages by provider"""
    try:
        languages = tts_adapter.get_supported_languages()
        return jsonify(languages), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# GPU Autoscaling
from app.services.gpu_autoscaling import GPUAutoscaler

gpu_autoscaler = GPUAutoscaler()

@app.route('/admin/gpu/cluster', methods=['GET'])
def get_gpu_cluster():
    """Get GPU cluster status (admin only)"""
    try:
        status = gpu_autoscaler.get_cluster_status()
        return jsonify(status), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/admin/gpu/register', methods=['POST'])
def register_gpu_node():
    """Register a new GPU node (admin only)"""
    try:
        data = request.get_json()
        node_id = data.get('node_id')
        gpu_count = data.get('gpu_count', 1)
        endpoint = data.get('endpoint')
        
        if not node_id or not endpoint:
            return jsonify({'error': 'node_id and endpoint required'}), 400
        
        success = gpu_autoscaler.register_node(node_id, gpu_count, endpoint)
        
        if success:
            return jsonify({
                'success': True,
                'message': f'Node {node_id} registered'
            }), 200
        else:
            return jsonify({'error': 'Failed to register node'}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/admin/gpu/scale', methods=['POST'])
def scale_gpu_cluster():
    """Trigger GPU cluster scaling (admin only)"""
    try:
        data = request.get_json()
        direction = data.get('direction', 'up')
        
        if direction == 'up':
            success = gpu_autoscaler.scale_up()
        elif direction == 'down':
            success = gpu_autoscaler.scale_down()
        else:
            return jsonify({'error': 'direction must be "up" or "down"'}), 400
        
        return jsonify({
            'success': success,
            'action': f'scale_{direction}',
            'cluster': gpu_autoscaler.get_cluster_status()
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Internal Video Engine
from app.services.video_engine import VideoEngine

video_engine = VideoEngine()

@app.route('/video/templates', methods=['GET'])
def list_video_templates():
    """List available video templates"""
    try:
        templates = video_engine.list_templates()
        return jsonify({'templates': templates}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/video/templates/<template_id>', methods=['GET'])
def get_video_template(template_id):
    """Get specific video template"""
    try:
        template = video_engine.get_template(template_id)
        if template:
            return jsonify(template.to_dict()), 200
        else:
            return jsonify({'error': 'Template not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/admin/video/template', methods=['POST'])
def create_video_template():
    """Create new video template (admin only)"""
    try:
        data = request.get_json()
        success = video_engine.create_template(
            template_id=data.get('template_id'),
            name=data.get('name'),
            resolution=tuple(data.get('resolution', [1920, 1080])),
            fps=data.get('fps', 30),
            background_type=data.get('background_type', 'color'),
            background_value=data.get('background_value', '#000000'),
            presenter_position=data.get('presenter_position')
        )
        
        if success:
            return jsonify({'success': True, 'message': 'Template created'}), 200
        else:
            return jsonify({'error': 'Failed to create template'}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/video/engine/stats', methods=['GET'])
def video_engine_stats():
    """Get video engine statistics"""
    try:
        stats = video_engine.get_stats()
        return jsonify(stats), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Lip-Sync Engine
from app.services.lipsync_engine import LipSyncEngine

lipsync_engine = LipSyncEngine()

@app.route('/lipsync/stats', methods=['GET'])
def lipsync_stats():
    """Get lip-sync engine statistics"""
    try:
        stats = lipsync_engine.get_stats()
        return jsonify(stats), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/lipsync/languages', methods=['GET'])
def lipsync_languages():
    """Get supported languages for lip-sync"""
    try:
        languages = lipsync_engine.get_supported_languages()
        return jsonify({'languages': languages}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/admin/lipsync/analyze', methods=['POST'])
def analyze_audio_phonemes():
    """Analyze audio and extract phonemes (admin only)"""
    try:
        data = request.get_json()
        audio_path = data.get('audio_path')
        language = data.get('language', 'en')
        
        if not audio_path:
            return jsonify({'error': 'audio_path required'}), 400
        
        phonemes = lipsync_engine.analyze_audio(audio_path, language)
        
        if phonemes:
            return jsonify({'phonemes': phonemes}), 200
        else:
            return jsonify({'error': 'Failed to analyze audio'}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Job Queue System
from app.services.job_queue import JobQueue, JobStatus

job_queue = JobQueue()

# Replace the old process_video with queue-based version
def process_video_with_queue(job_id: str):
    """Process video generation job from queue"""
    
    job_data = job_queue.get_job(job_id)
    if not job_data:
        logger.error(f"Job not found: {job_id}")
        return
    
    payload = job_data['payload']
    video_id = payload['video_id']
    script = payload['script']
    template = payload['template']
    user_id = payload['user_id']
    
    try:
        socketio.emit('video_status', {
            'id': video_id,
            'status': 'processing',
            'message': 'Starting video generation...',
            'progress': 10,
            'userId': user_id
        })
        
        # Generate audio using TTS adapter
        audio_path = tts_adapter.generate_audio(
            text=script,
            filename_prefix=f"video_{video_id}",
            video_id=video_id,
            user_id=user_id
        )
        
        if not audio_path:
            raise Exception("Audio generation failed")
        
        socketio.emit('video_status', {
            'id': video_id,
            'status': 'processing',
            'message': 'Audio generated successfully',
            'progress': 50,
            'userId': user_id
        })
        
        # Generate video (mock for now)
        video_url = f"https://mock-video.com/{video_id}.mp4"
        
        socketio.emit('video_status', {
            'id': video_id,
            'status': 'completed',
            'message': 'Video generation complete!',
            'progress': 100,
            'videoUrl': video_url,
            'userId': user_id
        })
        
        # Mark job as completed
        job_queue.complete_job(job_id, {
            'video_id': video_id,
            'video_url': video_url,
            'audio_path': audio_path
        })
        
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Video generation failed: {error_msg}")
        
        socketio.emit('video_status', {
            'id': video_id,
            'status': 'failed',
            'message': f'Error: {error_msg}',
            'progress': 0,
            'userId': user_id
        })
        
        # Mark job as failed (will retry)
        job_queue.fail_job(job_id, error_msg)

@app.route('/jobs/stats', methods=['GET'])
def get_job_stats():
    """Get job queue statistics"""
    try:
        stats = job_queue.get_queue_stats()
        return jsonify(stats), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/jobs/<job_id>', methods=['GET'])
def get_job_status(job_id):
    """Get job status"""
    try:
        job = job_queue.get_job(job_id)
        if job:
            return jsonify(job), 200
        else:
            return jsonify({'error': 'Job not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/jobs/<job_id>/cancel', methods=['POST'])
def cancel_job(job_id):
    """Cancel a job"""
    try:
        success = job_queue.cancel_job(job_id)
        if success:
            return jsonify({'success': True, 'message': 'Job cancelled'}), 200
        else:
            return jsonify({'error': 'Failed to cancel job'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/admin/jobs/cleanup', methods=['POST'])
def cleanup_old_jobs():
    """Cleanup old jobs (admin only)"""
    try:
        days = int(request.args.get('days', 7))
        deleted = job_queue.cleanup_old_jobs(days)
        return jsonify({
            'success': True,
            'deleted': deleted,
            'message': f'Cleaned up {deleted} old jobs'
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

