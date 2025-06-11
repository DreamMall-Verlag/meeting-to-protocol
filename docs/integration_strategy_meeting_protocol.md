# Integrationsstrategie: Meeting-to-Protocol als Microservice in DreamMall

## 1. Einführung

Dieses Dokument beschreibt die Strategie zur Integration der bestehenden Python-Anwendung "Meeting-to-Protocol" (Link zum Repo: [https://github.com/ogerly/Meeting-to-Protocol](https://github.com/ogerly/Meeting-to-Protocol)) in die DreamMall-Plattform. Angesichts der begrenzten Budget- und Entwicklerressourcen wird ein Ansatz gewählt, der auf die schnelle Nutzbarmachung der Kernfunktionalität als separater, über API ansprechbarer Dienst abzielt.

## 2. Gewählte Strategie: Server-zentrierter Microservice

Die "Meeting-to-Protocol"-Anwendung wird als eigenständiger Microservice auf einem Server betrieben. Das DreamMall-Backend (Node.js) wird über definierte API-Endpunkte mit diesem Microservice kommunizieren. Die rechenintensive Audioverarbeitung (Sprecherdiarisierung, Transkription) findet vollständig auf dem Server statt, der den Microservice hostet.

### 2.1 Begründung für diese Strategie

*   **Geringster initialer Entwicklungsaufwand:** Nutzt den vorhandenen Python-Code der Flask-Anwendung mit minimalen Umbauten zur Bereitstellung als API. Vermeidet komplexe Portierungen (Node.js) oder anspruchsvolle Client-Integrationen (Browser/lokales Programm).
*   **Schnelle Bereitstellung ("Time-to-Market"):** Ermöglicht eine zügige Integration der Kernfunktion in DreamMall.
*   **Kapselung der Komplexität:** Die spezialisierte Audioverarbeitungslogik bleibt im Python-Service isoliert.
*   **Zentrale Wartung und Updates:** Modelle und Code des Microservice können zentral verwaltet und aktualisiert werden.

### 2.2 Nachteile und zukünftige Überlegungen

*   **Serverkosten:** DreamMall trägt die Kosten für das Hosting und die Ausführung des rechenintensiven Microservice. Dies kann bei starker Nutzung signifikant werden.
*   **Skalierbarkeit:** Die Skalierung des Microservice erfordert entsprechende Serverinfrastruktur.
*   **Keine Nutzung lokaler Ressourcen:** Die Rechenleistung der Nutzer wird für die Audioverarbeitung nicht genutzt.

Zukünftige Strategien zur Kostenoptimierung (z.B. Hybrid-Ansätze, Auslagerung auf den Client) können evaluiert werden, sobald die Funktion etabliert ist und Nutzungsdaten vorliegen.

## 3. Architektur

```
DreamMall Frontend (Vue.js)
      |
      V
DreamMall Backend (Node.js/Express)
      | (HTTP/S API Calls)
      V
Meeting-to-Protocol Microservice (Python/Flask)
      |
      V
Audio Processing (PyAnnote, Whisper)
External LLM Services (optional, for Summary)
```

Das DreamMall-Backend dient als Orchestrator. Es nimmt Anfragen vom Frontend entgegen, leitet die relevanten Daten (Audiodatei, Parameter) an den Microservice weiter und verarbeitet/speichert die Ergebnisse, die vom Microservice zurückkommen, bevor sie an das Frontend gesendet werden.

## 4. API-Spezifikation des Meeting-to-Protocol Microservice

Der Microservice wird eine RESTful API über HTTP/S bereitstellen. Alle Anfragen sollten eine Form der Authentifizierung verwenden (z.B. API Key), um sicherzustellen, dass nur autorisierte DreamMall-Backend-Instanzen darauf zugreifen können.

**Basis-URL:** `[Wird im Deployment festgelegt, z.B. https://protocol-service.dreammall.com]`

### 4.1 Endpunkt: Audio-Upload und Verarbeitung starten

*   **Ziel:** Eine Audiodatei hochladen und den asynchronen Verarbeitungsprozess (Diarisierung, Transkription) starten.
*   **Methode:** `POST`
*   **Pfad:** `/process`
*   **Anfrage (Request):**
    *   `Content-Type: multipart/form-data`
    *   Formular-Daten:
        *   `audio_file`: Die hochzuladende Audiodatei (MP3 oder WAV).
        *   `user_id` (optional): Eine ID zur Identifizierung des DreamMall-Nutzers (für Logging oder spätere Zuordnung).
        *   `project_id` (optional): Eine ID zur Zuordnung zu einem spezifischen DreamMall-Projekt.
        *   `model_size` (optional): Gewünschte Größe des Whisper-Modells (`tiny`, `base`, `small`, `medium`, `large`). Standard: `base` (oder ein konfigurierbarer Wert).
*   **Antwort (Response):**
    *   **Erfolg (HTTP 202 Accepted):**
        ```json
        {
          "status": "processing_started",
          "job_id": "uuid-eindeutige-identifikation-des-jobs",
          "message": "Audio upload successful. Processing started."
        }
        ```
        *   `job_id`: Eine eindeutige ID, die verwendet wird, um den Status abzufragen und die Ergebnisse abzurufen.
    *   **Fehler (HTTP 400 Bad Request, 500 Internal Server Error etc.):**
        ```json
        {
          "status": "error",
          "message": "Detaillierte Fehlermeldung"
        }
        ```

### 4.2 Endpunkt: Verarbeitungsstatus abfragen

*   **Ziel:** Den aktuellen Status eines Verarbeitungsvorgangs anhand seiner `job_id` abfragen.
*   **Methode:** `GET`
*   **Pfad:** `/status/{job_id}`
*   **Anfrage (Request):** Keine Body-Daten. Die `job_id` ist Teil des Pfades.
*   **Antwort (Response):**
    *   **Erfolg (HTTP 200 OK):**
        ```json
        {
          "job_id": "uuid-eindeutige-identifikation-des-jobs",
          "status": "processing" | "completed" | "failed",
          "progress" (optional): 0-100 (Schätzung des Fortschritts),
          "message" (optional): Aktueller Status oder Fehlermeldung bei "failed"
        }
        ```
    *   **Job nicht gefunden (HTTP 404 Not Found):**
        ```json
        {
          "status": "error",
          "message": "Job ID not found."
        }
        ```

### 4.3 Endpunkt: Verarbeitungsergebnisse abrufen

*   **Ziel:** Die finalen Ergebnisse (Transkript mit Sprecherzuordnung) eines abgeschlossenen Verarbeitungsvorgangs abrufen.
*   **Methode:** `GET`
*   **Pfad:** `/results/{job_id}`
*   **Anfrage (Request):** Keine Body-Daten. Die `job_id` ist Teil des Pfades.
*   **Antwort (Response):**
    *   **Erfolg (HTTP 200 OK):**
        ```json
        {
          "job_id": "uuid-eindeutige-identifikation-des-jobs",
          "status": "completed", // Sollte immer "completed" sein, wenn Ergebnisse verfügbar sind
          "protocol": [
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
              "text": "Hallo zusammen."
            },
            // ... weitere Segmente
          ],
          "summary" (optional): "Zusammenfassung des Meetings...",
          "word_timestamps" (optional): true/false (Gibt an, ob Wort-Zeitstempel enthalten sind)
        }
        ```
        *   `protocol`: Array von Segmenten, wobei jedes Segment den Sprecher, Start-/Endzeit und den transkribierten Text enthält.
        *   `summary`: Optionale Zusammenfassung, falls vom Microservice generiert.
    *   **Job nicht abgeschlossen (HTTP 409 Conflict):**
        ```json
        {
          "job_id": "uuid-eindeutige-identifikation-des-jobs",
          "status": "processing" | "failed",
          "message": "Processing not yet completed or failed."
        }
        ```
    *   **Job nicht gefunden (HTTP 404 Not Found):**
        ```json
        {
          "status": "error",
          "message": "Job ID not found."
        }
        ```

### 4.4 Endpunkt: Zusammenfassung für abgeschlossenes Protokoll anfordern (optional)

*   **Ziel:** Eine Zusammenfassung für ein bereits verarbeitetes Protokoll anfordern (falls die Zusammenfassung nicht automatisch bei der Verarbeitung erstellt wird).
*   **Methode:** `POST`
*   **Pfad:** `/summarize/{job_id}`
*   **Anfrage (Request):**
    *   `Content-Type: application/json`
    *   Body (optional):
        ```json
        {
          "llm_model" (optional): "gpt-4o" | "..." (Modell für die Zusammenfassung),
          "prompt_instructions" (optional): "Fasse die wichtigsten Entscheidungen zusammen..."
        }
        ```
*   **Antwort (Response):**
    *   **Erfolg (HTTP 200 OK oder 202 Accepted, falls asynchron):**
        ```json
        {
          "job_id": "uuid-eindeutige-identifikation-des-jobs",
          "status": "summary_processing_started" | "summary_completed",
          "summary" (optional): "Die generierte Zusammenfassung...",
          "message" (optional): "Summary processing started."
        }
        ```
    *   **Fehler (HTTP 404, 409, 500 etc.):** Fehlerobjekt wie oben.

## 5. Code-Vorbereitung in der Python-Anwendung

Die bestehende Flask-Anwendung (`app.py`) muss angepasst werden, um als API zu fungieren:

1.  **Entfernen/Deaktivieren der HTML-Templates:** Die Routen sollten JSON-Antworten zurückgeben, keine HTML-Seiten rendern. Die `templates/index.html` und die zugehörigen Routen sind für die API-Nutzung nicht relevant.
2.  **API-Endpunkte implementieren:** Die neuen Endpunkte (`/process`, `/status/{job_id}`, `/results/{job_id}`, optional `/summarize/{job_id}`) müssen in Flask definiert werden.
3.  **Datei-Upload-Handling anpassen:** Die `/process` Route muss Datei-Uploads über `multipart/form-data` empfangen und speichern (temporär oder persistent, je nach Design).
4.  **Asynchrone Verarbeitung:** Die Audioverarbeitung (Diarisierung, Transkription) kann lange dauern. Der `/process` Endpunkt sollte die Datei speichern, einen Verarbeitungsprozess (z.B. in einem separaten Thread, Prozess oder über eine Task Queue wie Celery für Robustheit) starten und sofort eine `job_id` mit Status `processing_started` zurückgeben (HTTP 202).
5.  **Status- und Ergebnismanagement:** Der Status und die Ergebnisse jedes Jobs müssen gespeichert werden (z.B. in einer einfachen Datei-Struktur, einer lokalen SQLite-DB oder einer Redis-Instanz). Die `/status` und `/results` Endpunkte lesen aus dieser Speicherung.
6.  **Fehlerbehandlung:** Robuste Fehlerbehandlung für Datei-Uploads, Verarbeitungsfehler und ungültige Job-IDs implementieren. JSON-Fehlerantworten zurückgeben.
7.  **Authentifizierung:** Eine einfache API-Schlüssel-Authentifizierung implementieren, bei der das DreamMall Backend einen vordefinierten Schlüssel im Header jeder Anfrage mitsendet (`X-API-Key: dein_geheimer_schlüssel`). Der Microservice prüft diesen Schlüssel.
8.  **Logging:** Sinnvolles Logging für Anfragen, Verarbeitungsschritte und Fehler implementieren.
9.  **Dependencies:** Sicherstellen, dass alle Python-Dependencies (`requirements.txt`) korrekt installiert werden können und mit der Ausführungsumgebung des Servers kompatibel sind.

## 6. Implementierung im DreamMall Backend (Node.js)

Das DreamMall Backend wird die API des Microservice nutzen:

1.  **HTTP-Client:** Einen HTTP-Client (z.B. `axios`) installieren und konfigurieren.
2.  **Microservice URL und API Key konfigurieren:** Die Basis-URL des Microservice und der API-Schlüssel werden als Umgebungsvariablen im DreamMall Backend hinterlegt.
3.  **Neue API-Endpunkte für DreamMall:** Erstellen Sie DreamMall-Backend-Endpunkte (z.B. `/api/meetings/:meetingId/protocol`, `/api/users/:userId/protocol`) die als Proxy zum Microservice dienen.
4.  **Dateihandling:** Empfangen Sie die Audiodatei vom DreamMall Frontend, speichern Sie sie temporär oder streamen Sie sie direkt an den Microservice `/process` Endpunkt.
5.  **Job-ID Speicherung:** Speichern Sie die vom Microservice zurückgegebene `job_id` in der DreamMall-Datenbank (Supabase), verknüpft mit dem Nutzer, Meeting oder Projekt.
6.  **Status-Abfrage Logik:** Implementieren Sie Logik, die es dem DreamMall Frontend erlaubt, über das DreamMall Backend den Status des Jobs beim Microservice abzufragen (`/status`).
7.  **Ergebnis-Abholung und Speicherung:** Wenn der Status `completed` ist, rufen Sie die Ergebnisse (`/results`) ab und speichern Sie das finale Protokoll strukturiert in der DreamMall-Datenbank.
8.  **Fehlerbehandlung:** Behandeln Sie Fehler vom Microservice und geben Sie geeignete Antworten an das DreamMall Frontend zurück.
9.  **Authentifizierung:** Senden Sie den konfigurierten API-Schlüssel bei jeder Anfrage an den Microservice mit.

## 7. Implementierung im DreamMall Frontend (Vue.js)

Das DreamMall Frontend wird die neuen DreamMall Backend-Endpunkte nutzen:

1.  **Upload-Komponente:** Eine UI zum Hochladen der Audiodatei an das DreamMall Backend.
2.  **Statusanzeige:** Eine UI, die basierend auf der gespeicherten `job_id` regelmäßig den Verarbeitungsstatus über das DreamMall Backend abfragt und anzeigt.
3.  **Protokoll-Darstellung:** Eine UI zur Anzeige des finalen strukturierten Protokolls nach Abschluss der Verarbeitung.

## 8. Deployment

*   Der Meeting-to-Protocol Microservice muss separat vom DreamMall Backend deployed werden.
*   Ein einfacher Webserver (wie Gunicorn) und ein Reverse Proxy (Nginx, Caddy) sind für die Bereitstellung der Flask-App als Microservice erforderlich.
*   Sicherstellen, dass der Microservice nur über das interne Netzwerk oder gesichert (HTTPS + API Key) erreichbar ist.

```

```
