<!-- filepath: d:\Entwicklung\Projekte\DREAMMALL\luna-1\meeting-to-protocol\docs\meeting_protocol_microservice_guide.md -->
<!--
@LLMDOC
{
  "description": "Anleitung für die Installation, Konfiguration und Verwendung des Meeting-to-Protocol Microservices",
  "version": "1.0.0",
  "date": "2025-06-14",
  "tags": ["microservice", "meeting-protocol", "installation", "konfiguration", "api", "whisper"]
}
-->

# Meeting-Protocol Microservice Guide

## Einführung

Der Meeting-to-Protocol Microservice ist ein spezialisierter Service zum Konvertieren von Audio-Aufnahmen in strukturierte Meeting-Protokolle. Er verwendet moderne KI-Technologien wie OpenAI Whisper für die Transkription und LLMs für die Strukturierung und Zusammenfassung von Inhalten.

Dieser Guide behandelt die Installation, Konfiguration und Verwendung des Microservices.

## Voraussetzungen

- Python 3.10 oder höher
- FFmpeg installiert und im PATH
- 4 GB RAM oder mehr
- 10 GB freier Festplattenspeicher
- Internet-Verbindung für OpenAI API-Zugriff
- Docker (optional, aber empfohlen)

## Installation

### Standard-Installation (lokal)

1. Repository klonen:
   ```bash
   git clone https://github.com/dreammall/meeting-to-protocol.git
   cd meeting-to-protocol
   ```

2. Virtuelle Umgebung erstellen und aktivieren:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Unter Windows: venv\Scripts\activate
   ```

3. Abhängigkeiten installieren:
   ```bash
   pip install -r requirements.txt
   ```

4. Umgebungsvariablen konfigurieren:
   Kopiere die Datei `.env.example` nach `.env` und passe die Werte an, insbesondere den `API_KEY` für die Authentifizierung.

5. Start des Services:
   ```bash
   ./start.sh  # Unter Windows: start.bat
   ```

### Docker-Installation

1. Docker-Image bauen:
   ```bash
   docker build -t dreammall/meeting-protocol:latest .
   ```

2. Container starten:
   ```bash
   docker run -p 5000:5000 --env-file .env -v ./uploads:/app/uploads \
     -v ./results:/app/results -v ./logs:/app/logs \
     dreammall/meeting-protocol:latest
   ```

## Projektstruktur

```
meeting-to-protocol/
├── app.py                # Haupt-Flask-Anwendung
├── processing.py         # Audio- und Transkriptionsverarbeitung
├── models.py             # Datenmodelle
├── requirements.txt      # Python-Abhängigkeiten
├── start.sh             # Startskript
├── .env                 # Umgebungsvariablen
├── .gitignore           # Git-Ignore-Datei
├── uploads/             # Temporärer Speicher für hochgeladene Audiodateien
├── results/             # Temporärer Speicher für Transkriptionsergebnisse
├── logs/                # Logdateien
└── templates/           # HTML-Templates für einfache Weboberfläche
```

## Konfiguration

### Umgebungsvariablen

Die Datei `.env` enthält folgende Konfigurationsoptionen:

| Variable | Beschreibung | Standardwert |
|----------|--------------|--------------|
| `API_KEY` | API-Schlüssel für Authentifizierung | `dreammall_secret_key_123` |
| `UPLOAD_FOLDER` | Pfad zum Speichern von Uploads | `./uploads` |
| `RESULTS_FOLDER` | Pfad zum Speichern von Ergebnissen | `./results` |
| `LOG_LEVEL` | Protokollierungsebene | `INFO` |
| `PORT` | Port, auf dem der Server läuft | `5000` |
| `HOST` | Host zum Binden des Servers | `0.0.0.0` |
| `OPENAI_API_KEY` | OpenAI API-Schlüssel | - |
| `MAX_AUDIO_SIZE_MB` | Maximale Audio-Dateigröße in MB | `100` |

### Logging

Logs werden in der Datei `logs/microservice.log` gespeichert. Die Konfiguration kann in `app.py` angepasst werden.

## API-Endpoints

### 1. Audio verarbeiten

```
POST /process
```

**Headers:**
- `X-API-Key`: Der API-Schlüssel zur Authentifizierung

**Body (multipart/form-data):**
- `audio_file`: Audio-Datei (MP3, WAV, M4A, etc.)
- `user_id`: Benutzer-ID
- `project_id`: Projekt-ID (optional)
- `model_size`: Whisper-Modellgröße (tiny, base, small, medium, large)

**Antwort:**
```json
{
  "status": "processing_started",
  "job_id": "67924048-a921-4633-99a7-c346d82003e9",
  "message": "Audio upload successful. Processing started."
}
```

### 2. Status abrufen

```
GET /status/{job_id}
```

**Headers:**
- `X-API-Key`: Der API-Schlüssel zur Authentifizierung

**Antwort:**
```json
{
  "job_id": "67924048-a921-4633-99a7-c346d82003e9",
  "status": "processing",
  "message": "Transcribing audio",
  "progress": 60,
  "updated_at": "2025-06-12T16:20:42.756610"
}
```

### 3. Ergebnisse abrufen

```
GET /results/{job_id}
```

**Headers:**
- `X-API-Key`: Der API-Schlüssel zur Authentifizierung

**Antwort:**
```json
{
  "job_id": "67924048-a921-4633-99a7-c346d82003e9",
  "status": "completed",
  "protocol": {
    "metadata": { ... },
    "segments": [ ... ],
    "agenda_items": [ ... ],
    "action_items": [ ... ],
    "decisions": [ ... ]
  },
  "completed_at": "2025-06-12T16:25:42.756610"
}
```

### 4. Zusammenfassung generieren

```
POST /summarize/{job_id}
```

**Headers:**
- `X-API-Key`: Der API-Schlüssel zur Authentifizierung

**Body (JSON):**
```json
{
  "llm_model": "gpt-4o"  // Optionales Modell für die Zusammenfassung
}
```

**Antwort:**
```json
{
  "job_id": "67924048-a921-4633-99a7-c346d82003e9",
  "summary": "Dieses Meeting behandelte hauptsächlich die Projektplanung für Q3 mit Fokus auf neue Produktfeatures..."
}
```

### 5. Gesundheitsstatus

```
GET /health
```

**Antwort:**
```json
{
  "status": "ok",
  "version": "1.0.0",
  "uptime": "2d 4h 12m"
}
```

## Integration mit DreamMall

Der Microservice wird von der DreamMall-Backend-Anwendung angesprochen. Das Backend übernimmt:

1. Authentifizierung und Autorisierung von Benutzern
2. Speicherung von Protokollen in der Supabase-Datenbank
3. Verwaltung von Benutzer- und Projektzuordnungen
4. Kommunikation mit dem Frontend

Die Integration ist in der Datei `integration_strategy_meeting_protocol.md` detailliert beschrieben.

## Fehlerbehebung

### Typische Probleme und Lösungen

| Problem | Mögliche Ursache | Lösung |
|---------|------------------|--------|
| 401 Unauthorized | Falscher API-Schlüssel | API-Schlüssel in `.env` und Backend überprüfen |
| 413 Payload Too Large | Audio-Datei zu groß | `MAX_AUDIO_SIZE_MB` erhöhen oder Datei komprimieren |
| Transkriptionsfehler | Schlechte Audioqualität | Audio verbessern oder anderes Whisper-Modell wählen |
| Dienst startet nicht | Fehlende Abhängigkeiten | `pip install -r requirements.txt` erneut ausführen |
| FFmpeg-Fehler | FFmpeg nicht installiert | FFmpeg installieren und im PATH verfügbar machen |

### Log-Dateien

Bei Problemen prüfe die Log-Datei `logs/microservice.log` für detaillierte Fehlermeldungen.

## Best Practices

1. **Modellgröße auswählen**: 
   - `tiny`: Schnell, aber weniger genau. Gut für kurze Tests.
   - `base`: Ausgewogenes Verhältnis zwischen Geschwindigkeit und Genauigkeit.
   - `small`, `medium`: Höhere Genauigkeit für wichtige Meetings.
   - `large`: Höchste Genauigkeit, aber langsamste Verarbeitung.

2. **Audio-Qualität**:
   - Verwende hochwertige Aufnahmen, möglichst ohne Hintergrundgeräusche.
   - Ideale Formate sind WAV oder MP3 mit mindestens 128 kbps.

3. **Monitoring**:
   - Überwache den Speicherplatz im `uploads/` und `results/` Verzeichnis.
   - Prüfe regelmäßig die Log-Dateien auf Fehler oder Warnungen.

## Sicherheitshinweise

1. Der API-Schlüssel sollte sicher aufbewahrt und regelmäßig gewechselt werden.
2. Audiodateien werden nach der Verarbeitung automatisch gelöscht.
3. Der Microservice sollte hinter einer sicheren Firewall betrieben werden.
4. In Produktionsumgebungen sollte HTTPS verwendet werden.

## Skalierung

Für höhere Last kann der Service horizontal skaliert werden:

1. **Load Balancer**: Mehrere Instanzen hinter einem Load Balancer betreiben.
2. **Job Queue**: RabbitMQ oder Redis für die Auftragsverwaltung einsetzen.
3. **Container Orchestrierung**: Kubernetes für automatische Skalierung verwenden.

## Support und Weiterentwicklung

- Bug-Reports und Feature-Requests über das GitHub-Issue-System
- Regelmäßige Updates für neue Whisper-Modelle und verbesserte NLP-Funktionen
- Kontakt: support@dreammall.de


