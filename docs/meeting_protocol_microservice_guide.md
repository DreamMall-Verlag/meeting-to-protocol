halt des neuen Dokuments (Entwurf):

# DreamMall Microservice Guide: Meeting-to-Protocol

## 1. Einführung

Dieses Dokument dient als technischer Leitfaden für den Meeting-to-Protocol Microservice, der in die DreamMall-Plattform integriert wird. Es richtet sich primär an DreamMall-Entwickler, die diesen Dienst in das Backend und Frontend integrieren und nutzen wollen.

Der Microservice basiert auf der ursprünglichen Python-Anwendung [Meeting-to-Protocol](https://github.com/ogerly/Meeting-to-Protocol) und wurde angepasst, um als eigenständiger, über eine RESTful API ansprechbarer Dienst zu agieren. Seine Hauptaufgabe ist die **automatisierte Verarbeitung von Audioaufzeichnungen von Meetings zur Erstellung strukturierter Protokolle**, einschließlich Sprecherdiarisierung und Transkription. Eine optionale Zusammenfassungsfunktion ist ebenfalls verfügbar.

## 2. Funktionsweise des Microservice

Der Meeting-to-Protocol Microservice arbeitet wie folgt:

1.  **Audio-Upload:** Das DreamMall-Backend sendet eine Audioaufnahme eines Meetings (MP3 oder WAV) per HTTP-POST-Anfrage an den Microservice.
2.  **Job-Initiierung:** Der Microservice nimmt die Datei entgegen, speichert sie temporär und startet einen **asynchronen Verarbeitungsprozess** für diese Datei. Sofort danach antwortet der Microservice dem DreamMall-Backend mit einer eindeutigen **Job-ID** und dem Status, dass die Verarbeitung gestartet wurde (HTTP 202 Accepted).
3.  **Hintergrundverarbeitung:** Im Hintergrund führt der Microservice die rechenintensiven Schritte durch:
    *   **Sprecherdiarisierung (mit PyAnnote):** Identifizierung und Trennung der einzelnen Sprecher in der Audioaufnahme.
    *   **Transkription (mit Whisper):** Umwandlung der gesprochenen Sprache in Text für jedes Sprechersegment.
    *   **Protokollerstellung:** Strukturierung der transkribierten Segmente mit Sprecherzuordnung und Zeitstempeln.
4.  **Status-Tracking:** Das DreamMall-Backend kann den Status des Verarbeitungsprozesses jederzeit anhand der Job-ID beim Microservice abfragen.
5.  **Ergebnisabruf:** Sobald die Hintergrundverarbeitung abgeschlossen ist, kann das DreamMall-Backend das vollständige, strukturierte Protokoll (und optional eine Zusammenfassung) anhand der Job-ID vom Microservice abrufen.
6.  **Optional: Zusammenfassung:** Eine separate Anfrage kann an den Microservice gesendet werden, um eine Zusammenfassung des fertigen Protokolls zu generieren.
7.  **Ergebnisspeicherung in DreamMall:** Das DreamMall-Backend speichert die finalen Protokoll- und Zusammenfassungsergebnisse in der DreamMall-Datenbank (Supabase) und verknüpft sie mit dem entsprechenden Meeting, Nutzer oder Projekt.

Die asynchrone Verarbeitung ist entscheidend, da die Diarisierung und Transkription je nach Länge der Audioaufnahme und verfügbarer Serverressourcen einige Zeit in Anspruch nehmen kann.

## 3. Technologie-Stack des Microservice

*   **Backend Framework:** Flask (Python)
*   **Spracherkennung (ASR):** OpenAI Whisper
*   **Sprecherdiarisierung (SD):** PyAnnote.audio
*   **Asynchrone Verarbeitung:** Basierend auf Threads (einfache Implementierung) oder einer Task Queue (empfohlen für Produktion, z.B. Celery). Die aktuelle Implementierung nutzt Threads und Dateibasiertes Job-Management für schnelle Integration.
*   **Job-Management:** Aktuell rudimentär über JSON-Dateien für Status und Ergebnisse (Details siehe Abschnitt 5).
*   **Authentifizierung:** Einfache API Key Validierung.

## 4. API-Spezifikation

Der Microservice stellt eine RESTful API über HTTP/S bereit. Alle Anfragen vom DreamMall-Backend müssen einen gültigen API-Schlüssel im `X-API-Key` Header enthalten.

**Basis-URL:** `[Wird im Deployment festgelegt]`

### 4.1 Health Check

*   **Beschreibung:** Prüft, ob der Microservice läuft und erreichbar ist. Benötigt keinen API Key.
*   **Pfad:** `/health`
*   **Methode:** `GET`
*   **Authentifizierung:** Nein
*   **Antwort (HTTP 200 OK):**


json { "status": "ok", "message": "Microservice is running" }

*   **Antwort (Fehler):** Standard HTTP Fehlercodes (z.B. 500)

### 4.2 Audio-Upload und Verarbeitung starten

*   **Beschreibung:** Nimmt eine Audiodatei entgegen und startet den asynchronen Verarbeitungsprozess.
*   **Pfad:** `/process`
*   **Methode:** `POST`
*   **Authentifizierung:** API Key erforderlich (`X-API-Key` Header)
*   **Anfrage (Request Body - multipart/form-data):**
    *   `audio_file`: Die hochzuladende Audiodatei (MP3 oder WAV).
    *   `user_id` (optional): ID des DreamMall-Nutzers.
    *   `project_id` (optional): ID des DreamMall-Projekts.
    *   `model_size` (optional): Gewünschte Whisper-Modellgröße (`tiny`, `base`, `small`, `medium`, `large`).
*   **Antwort (HTTP 202 Accepted):**


json { "status": "processing_started", "job_id": "uuid-eindeutige-identifikation-des-jobs", "message": "Audio upload successful. Processing started." }

*   **Antwort (HTTP 400 Bad Request):** Bei fehlender `audio_file` oder leerem Dateinamen.


json { "status": "error", "message": "No audio_file part in the request" | "No selected file" }

*   **Antwort (HTTP 401 Unauthorized):** Bei fehlendem oder falschem API Key.
*   **Antwort (HTTP 500 Internal Server Error):** Bei Fehlern während des Dateispeicherns oder Startens des Hintergrundjobs.

### 4.3 Verarbeitungsstatus abfragen

*   **Beschreibung:** Fragt den aktuellen Status eines Jobs ab.
*   **Pfad:** `/status/{job_id}`
*   **Methode:** `GET`
*   **Authentifizierung:** API Key erforderlich (`X-API-Key` Header)
*   **Anfrage:** Die `job_id` ist Teil des Pfades. Keine Body-Daten.
*   **Antwort (HTTP 200 OK):**


json { "job_id": "...", "status": "processing" | "completed" | "failed", "progress" (optional): 0-100 (Schätzung), "message" (optional): Aktueller Status oder Fehlermeldung }

*   **Antwort (HTTP 401 Unauthorized):** Bei fehlendem oder falschem API Key.
*   **Antwort (HTTP 404 Not Found):** Wenn die `job_id` unbekannt ist.

### 4.4 Verarbeitungsergebnisse abrufen

*   **Beschreibung:** Ruft die vollständigen Verarbeitungsergebnisse (Protokoll) für einen abgeschlossenen Job ab.
*   **Pfad:** `/results/{job_id}`
*   **Methode:** `GET`
*   **Authentifizierung:** API Key erforderlich (`X-API-Key` Header)
*   **Anfrage:** Die `job_id` ist Teil des Pfades. Keine Body-Daten.
*   **Antwort (HTTP 200 OK):**


json { "job_id": "...", "status": "completed", // Sollte immer "completed" sein "protocol": [ { "speaker": "SPEAKER_XX", "start_time": float, "end_time": float, "text": "Transkribierter Text" }, // ... ], "summary" (optional): "Zusammenfassungstext...", "word_timestamps": boolean }

*   **Antwort (HTTP 401 Unauthorized):** Bei fehlendem oder falschem API Key.
*   **Antwort (HTTP 404 Not Found):** Wenn die `job_id` unbekannt ist.
*   **Antwort (HTTP 409 Conflict):** Wenn der Job-Status nicht "completed" ist.


json { "job_id": "...", "status": "processing" | "failed", "message": "Processing not yet completed or failed." }

*   **Antwort (HTTP 500 Internal Server Error):** Wenn Ergebnisse für einen abgeschlossenen Job nicht gefunden werden können.

### 4.5 Zusammenfassung anfordern (Optional)

*   **Beschreibung:** Fordert eine Zusammenfassung für ein bereits verarbeitetes Protokoll an.
*   **Pfad:** `/summarize/{job_id}`
*   **Methode:** `POST`
*   **Authentifizierung:** API Key erforderlich (`X-API-Key` Header)
*   **Anfrage (Request Body - application/json):**


json { "llm_model" (optional): "Gewünschtes LLM-Modell", "prompt_instructions" (optional): "Spezifische Anweisungen für die Zusammenfassung" }

*   **Antwort (HTTP 200 OK oder 202 Accepted):** Kann direkt die Zusammenfassung enthalten oder den Start der asynchronen Zusammenfassung bestätigen.


json { "job_id": "...", "status": "summary_processing_started" | "summary_completed", "summary" (optional): "Die generierte Zusammenfassung...", "message" (optional): "Summary processing started." }

*   **Antwort (HTTP 401 Unauthorized):** Bei fehlendem oder falschem API Key.
*   **Antwort (HTTP 404 Not Found):** Wenn die `job_id` unbekannt ist.
*   **Antwort (HTTP 409 Conflict):** Wenn der Job-Status des Protokolls nicht "completed" ist.
*   **Antwort (HTTP 500 Internal Server Error):** Bei Fehlern während der Zusammenfassungserstellung.

## 5. Job-Management und Persistenz

Die aktuelle Implementierung des Microservice nutzt eine **rudimentäre Dateibasis** zur Speicherung des Job-Status und der Verarbeitungsergebnisse.

*   Für jeden Job wird ein Unterordner im Verzeichnis `job_data` (oder dem konfigurierten `JOB_DIR`) erstellt.
*   Der Job-Status wird in `{job_id}_status.json` gespeichert.
*   Die vollständigen Verarbeitungsergebnisse werden in `{job_id}_results.json` gespeichert, sobald der Job abgeschlossen ist.

**Wichtiger Hinweis:** Diese Dateibasis ist für Entwicklungs- und Testzwecke gedacht und bietet eine einfache Persistenz bei Anwendungsneustarts. Für den produktiven Einsatz wird dringend empfohlen, auf eine robustere Lösung umzusteigen, wie z.B.:

*   **Datenbank:** Speicherung von Job-Metadaten und Ergebnissen in einer PostgreSQL, SQLite oder einer anderen Datenbank.
*   **Message Queue & Worker:** Einsatz einer Task Queue (wie Celery mit Redis/RabbitMQ als Broker) zur Verwaltung der Hintergrundaufgaben und zur Speicherung von Job-Status und Ergebnissen in einer geeigneten Datenbank/einem geeigneten Cache (z.B. Redis).

Diese robusteren Lösungen bieten bessere Skalierbarkeit, Fehlerbehandlung und Hochverfügbarkeit.

## 6. Authentifizierung

Der Microservice verwendet eine einfache API Key Authentifizierung. Das DreamMall-Backend muss den konfigurierten geheimen Schlüssel im `X-API-Key` Header jeder Anfrage mitsenden (Ausnahme: `/health`).

Der API Key wird über die Umgebungsvariable `MICROSERVICE_API_KEY` konfiguriert. Es ist entscheidend, dass dieser Schlüssel sicher verwaltet wird und nicht im Frontend exponiert wird.

## 7. Deployment-Überlegungen

*   Der Microservice muss auf einer Serverumgebung deployed werden, die Python 3.x und die benötigten Bibliotheken (PyTorch, FFmpeg etc.) unterstützt.
*   Für eine stabile Produktion sollte ein robuster WSGI-Server (wie Gunicorn oder Waitress) anstelle des Flask-Entwicklungsservers verwendet werden.
*   Ein Reverse Proxy (wie Nginx oder Caddy) sollte vor dem WSGI-Server platziert werden, um HTTPS zu terminieren, Lastverteilung zu ermöglichen und die statischen Dateien zu bedienen (auch wenn der Microservice primär eine API ist).
*   Sicherstellen, dass das `JOB_DIR` Verzeichnis auf dem Server beschreibbar ist und eine Strategie zur Bereinigung alter Job-Dateien implementiert wird.
*   Skalierungsstrategie planen: Bei hoher Last könnten zusätzliche Instanzen des Microservice hinter einem Load Balancer benötigt werden. Eine Task Queue würde hierbei die Lastverteilung der Verarbeitung erleichtern.

## 8. Integration im DreamMall Backend

Das DreamMall Backend wird als Client für diesen Microservice agieren. Die Implementierung im Node.js Backend umfasst:

*   Verwendung eines HTTP-Clients (`axios`, `node-fetch`).
*   Konfiguration der Microservice Basis-URL und des API Key (über Umgebungsvariablen).
*   Implementierung von Proxy-Endpunkten, die Anfragen vom DreamMall Frontend an den Microservice weiterleiten.
*   Handling der asynchronen Natur des Microservice: Anfragen an `/process` führen zur Speicherung der `job_id` in der DreamMall DB, und separate Logik zur Abfrage von `/status` und `/results` wird benötigt.
*   Speicherung der finalen Protokoll- und Zusammenfassungsergebnisse in der DreamMall Supabase-Datenbank.
*   Robuste Fehlerbehandlung für API-Aufrufe an den Microservice.

## 9. Integration im DreamMall Frontend

Das DreamMall Frontend (Vue.js) wird UI-Komponenten für:

*   Das Hochladen von Audiodateien an das DreamMall Backend (das dann an den Microservice weiterleitet).
*   Die Anzeige des Verarbeitungsstatus basierend auf den Informationen aus dem DreamMall Backend.
*   Die Darstellung des fertigen strukturierten Protokolls und der optionalen Zusammenfassung.


