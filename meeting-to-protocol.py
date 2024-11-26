import torch
from pyannote.audio import Pipeline
from dotenv import load_dotenv
import os
from pydub import AudioSegment
import whisper
from flask import Flask, request, render_template, jsonify, send_from_directory
from werkzeug.utils import secure_filename
import openai
import time
import json
import requests
from models import MODELS 

# Flask App Configuration
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = './uploads'
app.config['ALLOWED_EXTENSIONS'] = {'mp3', 'wav'}

# Load environment variables
load_dotenv()
HUGGINGFACE_API_KEY = os.getenv('HUGGINGFACE_API_KEY')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
openai.api_key = OPENAI_API_KEY

# Initialize Whisper Model
print("[INFO] Lade Whisper-Modell...")
whisper_model = whisper.load_model("base")
print("[INFO] Whisper-Modell erfolgreich geladen.")

# Initialize PyAnnote Pipeline
pipeline = None
if HUGGINGFACE_API_KEY:
    try:
        print("[INFO] Initialisiere pyannote Pipeline...")
        pipeline = Pipeline.from_pretrained("pyannote/speaker-diarization-3.1", use_auth_token=HUGGINGFACE_API_KEY)
        if torch.cuda.is_available():
            pipeline.to(torch.device("cuda"))
            print("[INFO] Pipeline zur GPU gesendet.")
        else:
            print("[WARNUNG] Keine GPU gefunden. Verwende CPU.")
    except Exception as e:
        print(f"[ERROR] Fehler beim Laden der pyannote Pipeline: {e}")
        print("[HINWEIS] Besuche https://huggingface.co/pyannote/speaker-diarization-3.1 und akzeptiere die Nutzungsbedingungen, falls notwendig.")
else:
    print("[ERROR] Kein HuggingFace API-Schlüssel gefunden. Bitte sicherstellen, dass die .env Datei korrekt ist.")

# Helper function to check allowed file extensions
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

@app.route('/')
def index():
  # Konvertiere MODELS in ein Format für das Frontend
    frontend_models = [
        {
            "id": model_id,
            "name": model_id,  # Kann später angepasst werden für benutzerfreundlichere Namen
            "api": config["api"]
        }
        for model_id, config in MODELS.items()
    ]
    return render_template(
        'index.html',
        title="Meeting Protokoll Generator",
        description="Laden Sie eine Meeting-Aufzeichnung hoch, und erstellen Sie ein strukturiertes und übersichtliches Meeting-Protokoll.",
        models=frontend_models
    )


@app.route('/uploads', methods=['POST'])
def upload():
    if 'audio' not in request.files:
        return jsonify({"error": "Keine Datei hochgeladen"}), 400

    file = request.files['audio']
    if file.filename == '':
        return jsonify({"error": "Keine Datei ausgewählt"}), 400

    if not allowed_file(file.filename):
        return jsonify({"error": "Ungültiger Dateityp"}), 400

    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)
    print(f"[INFO] Datei gespeichert unter: {filepath}")

    # Convert to WAV if needed
    if filepath.endswith('.mp3'):
        try:
            print("[INFO] Konvertiere MP3-Datei nach WAV...")
            audio = AudioSegment.from_file(filepath, format="mp3")
            wav_filepath = os.path.join(app.config['UPLOAD_FOLDER'], f"{os.path.splitext(filename)[0]}.wav")
            audio.export(wav_filepath, format="wav")
            print(f"[INFO] Konvertierung abgeschlossen. WAV-Datei gespeichert unter: {wav_filepath}")
        except Exception as e:
            return jsonify({"error": f"Fehler bei der Konvertierung: {e}"}), 500
    else:
        wav_filepath = filepath

    return jsonify({"message": "Datei erfolgreich hochgeladen", "wav_filepath": wav_filepath, "filename": os.path.basename(wav_filepath)})

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/analyze', methods=['POST'])
def analyze():
    data = request.json
    wav_filepath = data.get('wav_filepath')

    if not wav_filepath or not os.path.exists(wav_filepath):
        return jsonify({"error": "Audiodatei nicht gefunden"}), 400

    if pipeline is None:
        return jsonify({"error": "Die pyannote Pipeline wurde nicht initialisiert."}), 500

    try:
        print(f"[INFO] Starte Diarisierung für Datei: {wav_filepath}")
        diarization = pipeline(wav_filepath)
        print("[INFO] Diarisierung erfolgreich abgeschlossen.")

        # Transkription und Segmentzuordnung
        segments = []
        for turn, _, speaker in diarization.itertracks(yield_label=True):
            start = int(turn.start * 1000)  # in Millisekunden
            end = int(turn.end * 1000)      # in Millisekunden
            segment_audio = AudioSegment.from_file(wav_filepath)[start:end]
            segment_path = f"./uploads/temp_segment_{speaker}_{start}_{end}.wav"
            segment_audio.export(segment_path, format="wav")

            # Transkribiere das jeweilige Segment mit Whisper
            print(f"[INFO] Starte Transkription des Segments: {segment_path}")
            segment_result = whisper_model.transcribe(segment_path)
            segment_transcript = segment_result['text']
            print(f"[INFO] Transkription abgeschlossen: {segment_transcript}")

            # Speichern der Segmente und Transkripte
            segments.append({
                "start": turn.start,
                "end": turn.end,
                "speaker": speaker,
                "transcript": segment_transcript
            })

            # Lösche temporäre Datei
            os.remove(segment_path)

        # Rückgabe der Analyseergebnisse
        print("[INFO] Analyse erfolgreich abgeschlossen.")
        return jsonify({"segments": segments})
    except Exception as e:
        print(f"[ERROR] Fehler bei der Diarisierung oder Transkription: {e}")
        return jsonify({"error": f"Fehler bei der Diarisierung oder Transkription: {e}"}), 500

@app.route('/generate_summary', methods=['POST'])
def generate_summary():
    data = request.json
    segments = data.get('segments')
    model_id = data.get('model_type')
    custom_prompt = data.get('prompt')

    if not segments:
        return jsonify({"error": "Keine Segmente zur Zusammenfassung vorhanden"}), 400

    # Hole die Modell-Konfiguration
    if model_id not in MODELS:
        return jsonify({"error": f"Modell {model_id} nicht gefunden"}), 400
    
    model_config = MODELS[model_id]

    try:
        if model_config['api'] == 'openai':
            print(f"[INFO] Sende Anfrage an OpenAI (Modell: {model_id})...")
            response = openai.ChatCompletion.create(
                model=model_config['model_id'],
                messages=[
                    {"role": "system", "content": "Du bist ein hilfreicher Assistent, der Meetings zusammenfasst."},
                    {"role": "user", "content": custom_prompt}
                ],
                temperature=0.7
            )
            summary = response.choices[0].message['content'].strip()

        elif model_config['api'] == 'huggingface':
            print(f"[INFO] Sende Anfrage an Hugging Face (Modell: {model_id})...")
            headers = {
                "Authorization": f"Bearer {HUGGINGFACE_API_KEY}",
                "Content-Type": "application/json"
            }
            payload = {
                "inputs": custom_prompt,
                "parameters": {
                    "max_length": 150,
                    "min_length": 30,
                    "do_sample": False
                }
            }
            response = requests.post(
                f"https://api-inference.huggingface.co/models/{model_config['model_id']}",
                headers=headers,
                json=payload
            )
            response.raise_for_status()
            summary = response.json()[0]['summary_text']
        else:
            return jsonify({"error": f"API-Typ {model_config['api']} nicht unterstützt"}), 400

        return jsonify({"summary": summary})
    except Exception as e:
        print(f"[ERROR] Fehler bei der Zusammenfassungserstellung: {e}")
        return jsonify({"error": str(e)}), 500
if __name__ == '__main__':
    app.run(debug=True)
