from flask import Flask, request, jsonify, send_file
import os
import uuid
import threading
import datetime
import time
from pathlib import Path
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
import logging
import json
from processing import process_full_pipeline

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/microservice.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("protocol-microservice")

# Initialize Flask app
app = Flask(__name__)

# Constants and configuration
API_KEY = os.getenv("MICROSERVICE_API_KEY", "default_key_change_this")
JOB_DIR = os.getenv("JOB_DIR", "job_data")
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "uploads")
DEFAULT_WHISPER_MODEL = os.getenv("DEFAULT_WHISPER_MODEL", "base")
ALLOWED_EXTENSIONS = {'mp3', 'wav'}

# Create directories if they don't exist
for directory in [JOB_DIR, UPLOAD_DIR, "logs"]:
    os.makedirs(directory, exist_ok=True)

def allowed_file(filename):
    """Check if the file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def verify_api_key():
    """Verify the API key from the request header"""
    if request.endpoint == 'health_check':
        return True
        
    api_key = request.headers.get('X-API-Key')
    if not api_key or api_key != API_KEY:
        return False
    return True

def save_job_status(job_id, status, message=None, progress=None):
    """Save or update job status to a file"""
    status_data = {
        "job_id": job_id,
        "status": status,
        "updated_at": datetime.datetime.now().isoformat()
    }
    
    if message:
        status_data["message"] = message
    
    if progress is not None:
        status_data["progress"] = progress
    
    status_file = os.path.join(JOB_DIR, f"{job_id}_status.json")
    with open(status_file, 'w') as f:
        json.dump(status_data, f)

def save_job_results(job_id, protocol, summary=None):
    """Save job results to a file"""
    results_data = {
        "job_id": job_id,
        "status": "completed",
        "protocol": protocol,
        "completed_at": datetime.datetime.now().isoformat()
    }
    
    if summary:
        results_data["summary"] = summary
    
    results_file = os.path.join(JOB_DIR, f"{job_id}_results.json")
    with open(results_file, 'w') as f:
        json.dump(results_data, f)

def get_job_status(job_id):
    """Get job status from file"""
    status_file = os.path.join(JOB_DIR, f"{job_id}_status.json")
    if not os.path.exists(status_file):
        return None
    
    with open(status_file, 'r') as f:
        return json.load(f)

def get_job_results(job_id):
    """Get job results from file"""
    results_file = os.path.join(JOB_DIR, f"{job_id}_results.json")
    if not os.path.exists(results_file):
        return None
    
    with open(results_file, 'r') as f:
        return json.load(f)

def process_audio(job_id, audio_path, model_size=DEFAULT_WHISPER_MODEL):
    """Process audio file in a background thread"""
    try:
        # Skip actual processing in test mode for quick development
        if os.getenv("NODE_ENV") == "test":
            save_job_status(job_id, "processing", "Test mode: Simulating processing", 50)
            time.sleep(2)
            mock_protocol = [
                {
                    "speaker": "SPEAKER_00",
                    "start_time": 0.5,
                    "end_time": 4.2,
                    "text": "Hallo, willkommen zum Meeting."
                },
                {
                    "speaker": "SPEAKER_01",
                    "start_time": 4.5,
                    "end_time": 7.1,
                    "text": "Hallo zusammen. Ich freue mich, dass wir heute über das Projekt sprechen können."
                }
            ]
            save_job_results(job_id, mock_protocol)
            save_job_status(job_id, "completed", "Processing finished successfully", 100)
            return
        
        # Real processing begins here
        logger.info(f"Starting audio processing for job {job_id}")
        save_job_status(job_id, "processing", "Processing started", 5)
        
        save_job_status(job_id, "processing", "Loading models", 10)
        
        # Use the processing pipeline
        save_job_status(job_id, "processing", "Running processing pipeline", 30)
        protocol = process_full_pipeline(
            audio_path, 
            model_size, 
            os.getenv("DEFAULT_LANGUAGE", "de")
        )
        
        save_job_status(job_id, "processing", "Finalizing results", 90)
        save_job_results(job_id, protocol)
        save_job_status(job_id, "completed", "Processing finished successfully", 100)
        
        logger.info(f"Audio processing completed for job {job_id}")
    except Exception as e:
        logger.error(f"Error processing job {job_id}: {str(e)}")
        save_job_status(job_id, "failed", f"Error: {str(e)}")
    finally:
        # Clean up the audio file
        if os.path.exists(audio_path):
            try:
                os.remove(audio_path)
                logger.info(f"Removed audio file for job {job_id}")
            except Exception as e:
                logger.error(f"Failed to remove audio file for job {job_id}: {str(e)}")

@app.before_request
def check_auth():
    """Middleware to check authentication before each request"""
    if not verify_api_key() and request.endpoint != 'health_check':
        return jsonify({"status": "error", "message": "Unauthorized - Invalid API Key"}), 401

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint - doesn't require authentication"""
    return jsonify({
        "status": "ok",
        "message": "Meeting-to-Protocol microservice is running",
        "timestamp": datetime.datetime.now().isoformat()
    })

@app.route('/process', methods=['POST'])
def process():
    """Receive an audio file and start processing"""
    # Check if file is in the request
    if 'audio_file' not in request.files:
        return jsonify({"status": "error", "message": "No audio_file part in the request"}), 400
    
    file = request.files['audio_file']
    
    # If user doesn't select file, browser might send empty file
    if file.filename == '':
        return jsonify({"status": "error", "message": "No selected file"}), 400
    
    if file and allowed_file(file.filename):
        # Generate a unique job ID
        job_id = str(uuid.uuid4())
        
        # Create directories if they don't exist
        job_path = os.path.join(JOB_DIR, job_id)
        os.makedirs(job_path, exist_ok=True)
        
        # Save the file
        filename = secure_filename(file.filename)
        file_path = os.path.join(UPLOAD_DIR, f"{job_id}_{filename}")
        file.save(file_path)
        
        # Get optional parameters
        user_id = request.form.get('user_id', 'anonymous')
        project_id = request.form.get('project_id', 'none')
        model_size = request.form.get('model_size', DEFAULT_WHISPER_MODEL)
        
        # Log the upload
        logger.info(f"Received audio upload - job_id={job_id}, user_id={user_id}, project_id={project_id}")
        
        # Initialize job status
        save_job_status(job_id, "processing", "Audio file received, starting processing", 0)
        
        # Start processing in a background thread
        thread = threading.Thread(target=process_audio, args=(job_id, file_path, model_size))
        thread.start()
        
        return jsonify({
            "status": "processing_started",
            "job_id": job_id,
            "message": "Audio upload successful. Processing started."
        }), 202
    
    return jsonify({"status": "error", "message": "File type not allowed"}), 400

@app.route('/status/<job_id>', methods=['GET'])
def status(job_id):
    """Check the status of a job"""
    status_data = get_job_status(job_id)
    
    if not status_data:
        return jsonify({"status": "error", "message": "Job ID not found"}), 404
    
    return jsonify(status_data)

@app.route('/results/<job_id>', methods=['GET'])
def results(job_id):
    """Get the results of a completed job"""
    status_data = get_job_status(job_id)
    
    if not status_data:
        return jsonify({"status": "error", "message": "Job ID not found"}), 404
    
    if status_data["status"] != "completed":
        return jsonify({
            "job_id": job_id,
            "status": status_data["status"],
            "message": "Job is not completed yet"
        }), 409
    
    results_data = get_job_results(job_id)
    
    if not results_data:
        return jsonify({"status": "error", "message": "Results not found"}), 404
    
    return jsonify(results_data)

@app.route('/summarize/<job_id>', methods=['POST'])
def summarize(job_id):
    """Generate summary for a completed job"""
    status_data = get_job_status(job_id)
    
    if not status_data:
        return jsonify({"status": "error", "message": "Job ID not found"}), 404
    
    if status_data["status"] != "completed":
        return jsonify({
            "job_id": job_id,
            "status": status_data["status"],
            "message": "Cannot summarize incomplete job"
        }), 409
    
    results_data = get_job_results(job_id)
    
    if not results_data:
        return jsonify({"status": "error", "message": "Results not found"}), 404
    
    # Here we would send the transcript to a summarization model
    # For now, just mock it
    
    # Get any custom parameters
    request_data = request.get_json() or {}
    llm_model = request_data.get('llm_model', 'gpt-3.5-turbo')
    
    logger.info(f"Generating summary for job {job_id} using model {llm_model}")
    
    try:
        # In a real implementation, you'd call your summarization function here
        time.sleep(2)  # Simulate processing time
        
        summary = "Dies ist eine automatisch erstellte Zusammenfassung des Meetings. Die Teilnehmer haben die Integration des Meeting-to-Protocol Services besprochen."
        
        # Update results with summary
        results_data["summary"] = summary
        save_job_results(job_id, results_data["protocol"], summary)
        
        return jsonify({
            "job_id": job_id,
            "status": "summary_completed",
            "summary": summary
        })
    except Exception as e:
        logger.error(f"Error generating summary for job {job_id}: {str(e)}")
        return jsonify({
            "status": "error", 
            "message": f"Failed to generate summary: {str(e)}"
        }), 500

if __name__ == '__main__':
    port = int(os.getenv("PORT", 5000))
    host = os.getenv("HOST", "0.0.0.0")
    debug = os.getenv("DEBUG", "False").lower() in ('true', '1', 't')
    
    logger.info(f"Starting Meeting-to-Protocol microservice on {host}:{port}")
    app.run(host=host, port=port, debug=debug)
