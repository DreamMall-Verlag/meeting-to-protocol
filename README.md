# Meeting to Protocol

## Einleitung

Meeting-to-Protocol ist ein hochmoderner Microservice, der Audiodateien von Meetings automatisch in strukturierte, durchsuchbare Textprotokolle umwandelt. Durch den Einsatz fortschrittlicher Sprach-KI und natürlicher Sprachverarbeitung (NLP) reduziert dieser Service den Zeit- und Arbeitsaufwand für Meeting-Dokumentation erheblich.

## Funktionen

- **Automatische Transkription**: Umwandlung von Sprache in Text mit hoher Genauigkeit
- **Sprecherdiarisierung**: Erkennung und Trennung verschiedener Sprecher
- **Strukturierung**: Organisation des Inhalts in Tagesordnungspunkte, Aktionspunkte und Entscheidungen
- **Zusammenfassung**: KI-generierte Zusammenfassungen wichtiger Gesprächspunkte
- **RESTful API**: Einfache Integration in andere Anwendungen
- **Mehrsprachenunterstützung**: Verarbeitung von Meetings in verschiedenen Sprachen

## Installation

### Voraussetzungen

- Python 3.10 oder höher
- FFmpeg
- 4GB+ RAM
- OpenAI API-Zugang (optional, für erweiterte Funktionen)

### Schnelle Installation

```bash
# Repository klonen
git clone https://github.com/dreammall/meeting-to-protocol.git
cd meeting-to-protocol

# Virtuelle Umgebung erstellen
python -m venv venv
source venv/bin/activate  # Unter Windows: venv\Scripts\activate

# Abhängigkeiten installieren
pip install -r requirements.txt

# Umgebungsvariablen konfigurieren
cp .env.example .env
# Bearbeite .env mit deinen Einstellungen

# Service starten
./start.sh  # Unter Windows: start.bat
```

## Verwendung

### Als Standalone-Service

Der Service läuft standardmäßig auf `http://localhost:5000` und bietet eine einfache Web-Oberfläche für Tests.

### Als Teil von DreamMall

Dieser Microservice ist als Teil der DreamMall-Plattform konzipiert und kommuniziert mit dem DreamMall-Backend über definierte API-Endpunkte. Die Integration ist in der Datei `docs/integration_strategy_meeting_protocol.md` dokumentiert.

## API-Dokumentation

Die vollständige API-Dokumentation findet sich in `docs/meeting_protocol_microservice_guide.md`.

### Hauptendpunkte

- `POST /process`: Audio-Upload und Verarbeitung starten
- `GET /status/{job_id}`: Status eines Verarbeitungsjobs abfragen
- `GET /results/{job_id}`: Ergebnisse eines abgeschlossenen Jobs abrufen
- `POST /summarize/{job_id}`: Zusammenfassung für ein Protokoll generieren

## Konfiguration

Die Konfiguration erfolgt über Umgebungsvariablen in der `.env`-Datei:

- `API_KEY`: Schlüssel für API-Authentifizierung
- `UPLOAD_FOLDER`: Verzeichnis für hochgeladene Audiodateien
- `RESULTS_FOLDER`: Verzeichnis für Ergebnisse
- `LOG_LEVEL`: Protokollierungsebene (DEBUG, INFO, WARNING, ERROR)
- `PORT`: Server-Port
- `OPENAI_API_KEY`: OpenAI API-Schlüssel für erweiterte Funktionen

## Entwicklung

Beiträge zum Projekt sind willkommen! Bitte beachte:

1. Fork das Repository
2. Erstelle einen Feature-Branch
3. Teste deine Änderungen
4. Reiche einen Pull Request ein

## Lizenz

Copyright © 2025 DreamMall, alle Rechte vorbehalten.

