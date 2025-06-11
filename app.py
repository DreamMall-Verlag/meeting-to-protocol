from flask import Flask, request, jsonify, send_file
import os
import uuid
import threading
import time
import json

# Importiere deine existierende Verarbeitungslogik
# Beispiel: from your_processing_module import process_audio_task, get_job_status, get_job_results

app = Flask(__name__)
# Lade API Key aus Umgebungsvariable oder Konfigurationsdatei
API_KEY = os.environ.get("MICROSERVICE_API_KEY", "your_default_secret_key") # BITTE ÄNDERN!

# --- Job-Verwaltung mit JSON-Dateien ---
JOB_DIR = "job_data" # Oder ein anderer geeigneter Pfad

# Stelle sicher, dass das Verzeichnis für Job-Daten existiert
os.makedirs(JOB_DIR, exist_ok=True)

def get_job_status_from_file(job_id):
    """Liest den Job-Status aus einer JSON-Datei."""
    status_file = os.path.join(JOB_DIR, f"{job_id}_status.json")
    if os.path.exists(status_file):
        try:
            with open(status_file, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            print(f"Error reading status file {status_file}: {e}")
            return None
    return None

def save_job_status_to_file(job_id, status_data):
    """Speichert den Job-Status in einer JSON-Datei."""
    status_file = os.path.join(JOB_DIR, f"{job_id}_status.json")
    try:
        with open(status_file, 'w') as f:
            json.dump(status_data, f)
    except IOError as e:
        print(f"Error writing status file {status_file}: {e}")


def get_job_results_from_file(job_id):
    """Liest die Job-Ergebnisse aus einer JSON-Datei."""
    results_file = os.path.join(JOB_DIR, f"{job_id}_results.json")
    if os.path.exists(results_file):
        try:
            with open(results_file, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            print(f"Error reading results file {results_file}: {e}")
            return None
    return None

def save_job_results_to_file(job_id, results_data):
    """Speichert die Job-Ergebnisse in einer JSON-Datei."""
    results_file = os.path.join(JOB_DIR, f"{job_id}_results.json")
    try:
        with open(results_file, 'w') as f:
            json.dump(results_data, f)
    except IOError as e:
        print(f"Error writing results file {results_file}: {e}")

# --- Ende Job-Verwaltung mit JSON-Dateien ---


def check_api_key():
    """Prüft den X-API-Key Header."""
    if 'X-API-Key' not in request.headers or request.headers['X-API-Key'] != API_KEY:
        return jsonify({"status": "error", "message": "Unauthorized"}), 401
    return None # Rückgabe None bedeutet, dass die Prüfung erfolgreich war

# --- Middleware für API Key Prüfung ---
@app.before_request
def before_request_check():
    # Prüfe API Key für die definierten API Routen
    if request.path.startswith('/process') or request.path.startswith('/status') or request.path.startswith('/results') or request.path.startswith('/summarize'):
         auth_error = check_api_key()
         if auth_error:
             return auth_error

# --- HEALTH CHECK ENDPOINT (Ohne API Key) ---
@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "ok", "message": "Microservice is running"})


@app.route('/process', methods=['POST'])
def process_audio():
    if 'audio_file' not in request.files:
        return jsonify({"status": "error", "message": "No audio_file part in the request"}), 400

    file = request.files['audio_file']
    if file.filename == '':
        return jsonify({"status": "error", "message": "No selected file"}), 400

    if file:
        job_id = str(uuid.uuid4())
        # Temporären Dateipfad erstellen. Wichtig: Stellen Sie sicher, dass das Verzeichnis beschreibbar ist!
        # Verwenden Sie idealerweise einen dedizierten Ordner, nicht /tmp
        temp_audio_path = os.path.join(JOB_DIR, f"{job_id}_{file.filename}") # Speichern im Job-Verzeichnis

        try:
            file.save(temp_audio_path)

            # Optional: Metadaten extrahieren
            user_id = request.form.get('user_id')
            project_id = request.form.get('project_id')
            model_size = request.form.get('model_size', 'base') # Standardwert 'base'

            # Job-Status initialisieren und speichern
            initial_status = {"job_id": job_id, "status": "processing", "progress": 0, "message": "Upload successful, starting processing"}
            save_job_status_to_file(job_id, initial_status)

            # --- Hintergrundaufgabe starten ---
            # Für Robustheit in Produktion: Celery, RQ, etc. verwenden, die eine Message Queue nutzen.
            thread = threading.Thread(target=process_audio_background, args=(job_id, temp_audio_path, model_size))
            thread.start()
            # ----------------------------------

            return jsonify({
                "status": "processing_started",
                "job_id": job_id,
                "message": "Audio upload successful. Processing started."
            }), 202 # 202 Accepted, da Verarbeitung im Hintergrund läuft

        except Exception as e:
            # Fehler beim Speichern oder Starten des Jobs
            if os.path.exists(temp_audio_path):
                 os.remove(temp_audio_path) # Temporäre Datei löschen

            error_message = f"Failed to start processing: {str(e)}"
            print(f"Error for job {job_id}: {error_message}") # Loggen
            save_job_status_to_file(job_id, {"job_id": job_id, "status": "failed", "message": error_message}) # Status auf failed setzen
            return jsonify({"status": "error", "message": error_message}), 500


# --- Hintergrundaufgabe ---
def process_audio_background(job_id, audio_path, model_size):
    print(f"Starting background processing for job {job_id}")
    # Status aktualisieren
    save_job_status_to_file(job_id, {"job_id": job_id, "status": "processing", "progress": 5, "message": "Processing audio..."})

    try:
        # --- HIER INTEGRIEREN SIE IHRE VORHANDENE VERARBEITUNGSLOGIK ---
        # Rufen Sie Ihre Funktionen zur Diarisierung und Transkription auf.
        # Stellen Sie sicher, dass diese Funktionen den Pfad zur Audiodatei verwenden.
        # Sie müssen möglicherweise Ihre bestehende Logik anpassen,
        # um das Ergebnis im erwarteten JSON-Format zu erzeugen (siehe API-Spezifikation 4.3).

        # Beispiel:
        # diarization_result = run_diarization(audio_path)
        # transcription_result = run_transcription(audio_path, model_size)

        # Kombinieren Sie die Ergebnisse zu Ihrem finalen Protokoll-Format
        # final_protocol_data = combine_results(diarization_result, transcription_result)

        # --- Simulations-Dummy-Verarbeitung ---
        # ERSETZEN SIE DIES DURCH IHRE ECHTE LOGIK!
        time.sleep(10) # Simulieren Sie die Verarbeitungszeit
        final_protocol_data = [
            {"speaker": "SPEAKER_00", "start_time": 1.0, "end_time": 3.0, "text": "Dies ist ein Test."},
            {"speaker": "SPEAKER_01", "start_time": 3.5, "end_time": 5.5, "text": "Okay, verstanden."}
        ]
        # ------------------------------------

        # Ergebnisse speichern
        results_data = {
            "job_id": job_id,
            "status": "completed",
            "protocol": final_protocol_data,
            "summary": None, # Optionale Zusammenfassung
            "word_timestamps": False # Anpassen, falls Wort-Zeitstempel generiert werden
        }
        save_job_results_to_file(job_id, results_data)
        # Status auf completed setzen
        save_job_status_to_file(job_id, {"job_id": job_id, "status": "completed", "progress": 100, "message": "Processing completed"})
        print(f"Background processing completed for job {job_id}")

    except Exception as e:
        # Fehler während der Verarbeitung
        error_message = f"Processing failed: {str(e)}"
        print(f"Error during processing job {job_id}: {error_message}") # Loggen
        # Status auf failed setzen
        save_job_status_to_file(job_id, {"job_id": job_id, "status": "failed", "message": error_message})
        # Keine Ergebnisse im Fehlerfall speichern
        save_job_results_to_file(job_id, None)


    finally:
        # Temporäre Audiodatei löschen
        if os.path.exists(audio_path):
            try:
                os.remove(audio_path)
                print(f"Cleaned up audio file {audio_path}")
            except OSError as e:
                 print(f"Error removing audio file {audio_path}: {e}")


@app.route('/status/<job_id>', methods=['GET'])
def get_job_status(job_id):
    status = get_job_status_from_file(job_id) # Aus Datei lesen
    if status is None:
        return jsonify({"status": "error", "message": "Job ID not found."}), 404
    return jsonify(status)


@app.route('/results/<job_id>', methods=['GET'])
def get_job_results(job_id):
    status = get_job_status_from_file(job_id) # Aus Datei lesen

    if status is None:
        return jsonify({"status": "error", "message": "Job ID not found."}), 404

    if status["status"] != "completed":
        # Job ist noch nicht fertig oder fehlgeschlagen
        return jsonify({
            "job_id": job_id,
            "status": status["status"],
            "message": "Processing not yet completed or failed."
        }), 409 # 409 Conflict

    results = get_job_results_from_file(job_id) # Aus Datei lesen
    if results is None: # Sollte nicht passieren, wenn status="completed", aber zur Sicherheit
         return jsonify({"job_id": job_id, "status": "error", "message": "Results not available for completed job."}), 500

    return jsonify(results)

@app.route('/summarize/<job_id>', methods=['POST'])
def summarize_protocol(job_id):
    status = get_job_status_from_file(job_id) # Aus Datei lesen

    if status is None:
        return jsonify({"status": "error", "message": "Job ID not found."}), 404

    if status["status"] != "completed":
        return jsonify({
            "job_id": job_id,
            "status": status["status"],
            "message": "Cannot summarize. Processing not yet completed or failed."
        }), 409

    results = get_job_results_from_file(job_id) # Aus Datei lesen
    if results is None or 'protocol' not in results:
         return jsonify({"job_id": job_id, "status": "error", "message": "Protocol results not available for summarization."}), 500

    # --- HIER INTEGRIEREN SIE IHRE ZUSAMMENFASSUNGSLOGIK ---
    # Nehmen Sie den Text aus results['protocol'] und senden Sie ihn an Ihr LLM.
    # Sie können llm_model oder prompt_instructions aus request.json lesen, falls gesendet.

    try:
        # Beispiel: text_to_summarize = " ".join([seg['text'] for seg in results['protocol']])
        # summary_text = call_llm_for_summary(text_to_summarize, request.json.get('llm_model'), request.json.get('prompt_instructions'))

        # --- Simulations-Dummy-Zusammenfassung ---
        # ERSETZEN SIE DIES DURCH IHRE ECHTE LOGIK!
        time.sleep(5) # Simulieren Sie die Zusammenfassungszeit
        summary_text = "Dies ist eine generierte Test-Zusammenfassung des Meetings."
        # ------------------------------------

        # Speichern Sie die Zusammenfassung im Job-Ergebnis
        # Achtung: Ergebnisse erneut aus Datei lesen, da Hintergrundaufgabe diese geändert haben könnte
        current_results = get_job_results_from_file(job_id)
        if current_results is not None:
            current_results['summary'] = summary_text
            save_job_results_to_file(job_id, current_results)
        else:
             # Fehler: Ergebnisse verschwunden?
             raise Exception("Job results disappeared after status was completed.")


        return jsonify({
            "job_id": job_id,
            "status": "summary_completed", # Oder "processing" falls asynchron
            "summary": summary_text,
            "message": "Summary generated successfully."
        }), 200

    except Exception as e:
        error_message = f"Summary generation failed: {str(e)}"
        print(f"Error during summarization job {job_id}: {error_message}") # Loggen
        # Status des Jobs bleibt completed, aber Zusammenfassung fehlt oder ist null im Ergebnis
        return jsonify({"job_id": job_id, "status": "error", "message": error_message}), 500

# Die folgenden Teile (MODELS, PROMPT_TEMPLATE, HTML/JS) gehören zur ursprünglichen Web-UI und sollten für den Microservice entfernt oder ignoriert werden.
# Wenn Sie diese für andere Zwecke benötigen, lagern Sie sie in separate Dateien aus.

# MODELS = { ... } # Entfernen oder ignorieren
# PROMPT_TEMPLATE = ''' ... ''' # Entfernen oder ignorieren
# <!DOCTYPE html>...</html> # Entfernen oder ignorieren
