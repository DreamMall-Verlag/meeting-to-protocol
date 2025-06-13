<!-- filepath: d:\Entwicklung\Projekte\DREAMMALL\luna-1\meeting-to-protocol\docs\integration_strategy_meeting_protocol.md -->
<!--
@LLMDOC
{
  "description": "Strategie zur Integration des Meeting-to-Protocol Microservices in die DreamMall-Plattform",
  "version": "1.0.0",
  "date": "2025-06-14",
  "tags": ["integration", "microservice", "meeting-protocol", "architektur", "kommunikation", "datenfluss"]
}
-->

# Integrationsstrategie: Meeting-to-Protocol Microservice

## 1. Übersicht

Dieses Dokument beschreibt die Strategie zur Integration des Meeting-to-Protocol Microservices in die DreamMall-Plattform. Der Meeting-to-Protocol Microservice ist ein spezialisierter Service, der Audiodateien von Meetings in strukturierte, durchsuchbare Textprotokolle umwandelt.

## 2. Kommunikationsfluss

### 2.1 Schnittstellen-Übersicht

```
+-------------------+       +-------------------+       +-------------------+
| DreamMall         |       | DreamMall         |       | Meeting-to-       |
| Frontend (Vue.js) | <---> | Backend (Node.js) | <---> | Protocol (Python) |
+-------------------+       +-------------------+       +-------------------+
```

### 2.2 Detaillierter Datenfluss

1. **Frontend → Backend**:
   - Audio-Upload (multipart/form-data)
   - Status-Abfragen (GET-Request mit Job-ID)
   - Protokoll-Abrufe (GET-Request mit Job-ID)
   - Zusammenfassungs-Anfragen (POST-Request mit Job-ID)

2. **Backend → Microservice**:
   - Audio-Weiterleitung (multipart/form-data + API-Key)
   - Status-Abfragen (GET-Request mit API-Key)
   - Ergebnis-Abrufe (GET-Request mit API-Key)
   - Zusammenfassungs-Anfragen (POST-Request mit API-Key)

3. **Microservice → Backend**:
   - Job-Status-Updates (JSON-Antwort)
   - Transkriptions- und Protokollergebnisse (JSON-Antwort)
   - Zusammenfassungen (JSON-Antwort)

4. **Backend → Frontend**:
   - Status-Updates zur UI-Aktualisierung
   - Strukturierte Protokolldaten zur Anzeige
   - Fehler- und Erfolgsmeldungen

## 3. API-Endpunkte

### 3.1 Frontend → Backend API

| Endpunkt | Methode | Beschreibung | Parameter | Return |
|----------|---------|--------------|-----------|--------|
| `/api/meeting-protocol/upload` | POST | Audio-Upload | `audio_file` (File), `projectId` (optional), `modelSize` | `{ jobId, success, message }` |
| `/api/meeting-protocol/status/:jobId` | GET | Status-Abfrage | `jobId` (URL-Param) | `{ status, progress, message }` |
| `/api/meeting-protocol/results/:jobId` | GET | Ergebnis-Abruf | `jobId` (URL-Param) | `{ protocol, summary, ... }` |
| `/api/meeting-protocol/summarize/:jobId` | POST | Zusammenfassung | `jobId` (URL-Param), `model` (Body) | `{ summary }` |
| `/api/meeting-protocol/user-protocols` | GET | Benutzerprotokolle | - | `[{ jobId, status, created_at, ... }, ...]` |

### 3.2 Backend → Microservice API

| Endpunkt | Methode | Beschreibung | Header | Parameter | Return |
|----------|---------|--------------|--------|-----------|--------|
| `/process` | POST | Audio-Verarbeitung | `X-API-Key` | `audio_file` (File), `user_id`, `project_id` (optional), `model_size` | `{ job_id, status, message }` |
| `/status/:job_id` | GET | Status-Abfrage | `X-API-Key` | `job_id` (URL-Param) | `{ status, progress, message }` |
| `/results/:job_id` | GET | Ergebnis-Abruf | `X-API-Key` | `job_id` (URL-Param) | `{ protocol, ... }` |
| `/summarize/:job_id` | POST | Zusammenfassung | `X-API-Key` | `job_id` (URL-Param), `llm_model` (Body) | `{ summary }` |

## 4. Datenspeicherung und -verantwortung

### 4.1 Microservice-Speicherung (temporär)

- **Audio-Dateien**: Werden im `uploads/` Verzeichnis gespeichert und nach Verarbeitung gelöscht
- **Job-Status**: In Speicher oder temporärer Datenbank während der Verarbeitung
- **Transkriptionsergebnisse**: Temporär im `results/` Verzeichnis vor der Übertragung zum Backend

### 4.2 Backend-Speicherung (permanent)

- **Job-Metadaten**: In der `protocol_jobs` Tabelle in Supabase
- **Protokolle**: In der `protocols` Tabelle in Supabase als JSON
- **Benutzer- und Projektzuordnung**: In den entsprechenden Relationen der Tabellen

### 4.3 Datensicherheit

- Audiodateien werden nach der Verarbeitung vom Microservice gelöscht
- Nur das Backend speichert permanente Daten in der verschlüsselten Datenbank
- Zugriffskontrolle durch Row-Level-Security in Supabase
- API-Schlüssel-Authentifizierung zwischen Backend und Microservice

## 5. Fehlerbehandlung und Robustheit

### 5.1 Fehlerszenarien und Behandlung

| Fehlerszenario | Behandlungsstrategie |
|----------------|----------------------|
| Microservice nicht erreichbar | Backend gibt 503 Service Unavailable zurück + Retry-Mechanismus |
| Audio-Upload fehlgeschlagen | Backend fängt Fehler ab, Datei wird nicht gespeichert |
| Transkriptionsfehler | Microservice meldet Fehler, Backend aktualisiert Job-Status auf "failed" |
| Datenbank-Fehler | Backend liefert 500 Internal Server Error mit spezifischer Fehlermeldung |
| Timeout bei langer Verarbeitung | Exponentielles Backoff bei Status-Abfragen |

### 5.2 Monitoring

- Logs werden in beiden Systemen geführt
- Microservice schreibt in `logs/microservice.log`
- Backend nutzt den LoggerService
- Erfassung von Performance-Metriken (Verarbeitungszeiten, Erfolgsraten)

## 6. Deployment-Konfiguration

### 6.1 Umgebungsvariablen

#### Backend `.env`
```
MEETING_PROTOCOL_URL=http://localhost:5000
MEETING_PROTOCOL_API_KEY=dreammall_secret_key_123
```

#### Microservice `.env`
```
API_KEY=dreammall_secret_key_123
UPLOAD_FOLDER=./uploads
RESULTS_FOLDER=./results
LOG_LEVEL=INFO
```

### 6.2 Netzwerk-Konfiguration

- Im Development-Modus: Direkter HTTP-Zugriff über localhost
- In Produktion: Containerisiert mit Docker-Network oder über VPC
- Alternative: Sichere API-Gateway-Lösung

## 7. Implementierungsplan

1. **Microservice entwickeln und testen**
   - Implementierung der Python-Flask-API
   - Whisper und NLP-Integration
   - Lokales Testing der Audio-Verarbeitung

2. **Backend-Integration**
   - Service- und Controller-Implementierung
   - Supabase-Tabellen anlegen
   - Authentifizierung und Autorisierung

3. **Frontend-Integration**
   - Upload-Komponente entwickeln
   - Status-Tracking-UI implementieren
   - Protokoll-Anzeige und -Verwaltung

4. **End-to-End-Tests**
   - Vollständige Workflow-Tests mit realen Audiodateien
   - Performance und Load Testing

5. **Deployment und CI/CD**
   - Docker-Container für Microservice
   - Deployment-Pipeline konfigurieren
   - Monitoring-Setup

## 8. Schlussbemerkungen

Diese Integrationsstrategie definiert klar die Verantwortlichkeiten zwischen Frontend, Backend und dem Meeting-to-Protocol-Microservice. Das Backend fungiert als Vermittler und Datenspeicher, während der spezialisierte Python-Microservice die rechenintensive Verarbeitung übernimmt. Durch die klare Trennung und definierte APIs wird eine robuste, skalierbare und wartbare Lösung geschaffen.