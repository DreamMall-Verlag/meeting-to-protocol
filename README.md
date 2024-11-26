# Meeting to Protocol

## Einleitung

Dieses Projekt kombiniert die Leistungsfähigkeit von **PyAnnote** zur Sprecherdiarisierung und **Whisper** zur Audio-Transkription. Es wurde eine Webanwendung entwickelt, mit der Benutzer Audiodateien hochladen, analysieren und die Ergebnisse (z.B. Sprecherzuordnungen und Transkripte) visuell anzeigen lassen können. Die Anwendung ist mit Flask als Backend und einer einfachen HTML-Frontend-Benutzeroberfläche realisiert. 
## Funktionalitäten

- **Audiodateien hochladen**: Benutzer können MP3- oder WAV-Dateien hochladen, die dann automatisch in das WAV-Format umgewandelt werden, falls sie im MP3-Format vorliegen.
- **Audioplayer**: Nach dem Hochladen der Audiodatei wird eine Wellenformanzeige im Browser erstellt. Benutzer können die gesamte Datei oder spezifische Abschnitte der Audiodatei direkt im Browser abspielen.
- **Audioanalyse starten**: Nachdem die Datei hochgeladen wurde, kann der Benutzer die Analyse starten. Dabei werden die verschiedenen Sprecher in der Datei identifiziert und die jeweiligen gesprochenen Segmente transkribiert.
- **Prompt generieren**: Ein strukturierter Prompt wird basierend auf den transkribierten Segmenten generiert, um eine Zusammenfassung des Meetings zu erstellen.
- **Anbindung an HuggingFace und OpenAI**: Es gibt eine Anbindung an HuggingFace (für die Speaker-Diarisierung) und OpenAI (für die Zusammenfassung der Meetings), um modernste NLP-Modelle nutzen zu können.
- **Protokollausgabe**: Basierend auf dem generierten Prompt wird ein strukturiertes Protokoll des Meetings erstellt. Die Zusammenfassung wird als benutzerfreundliches Meeting-Protokoll ausgegeben.

## Technische wissenschaftliche Erklärung

Das Projekt nutzt zwei Kerntechnologien zur Audiobearbeitung:

1. **Sprecherdiarisierung mit PyAnnote**: PyAnnote verwendet maschinelles Lernen, um unterschiedliche Sprecher in einer Audiodatei zu identifizieren und die einzelnen Sprachsegmente zu trennen. Dies ermöglicht die Zuordnung von Beiträgen zu bestimmten Sprechern, was die Analyse von Meetings erheblich vereinfacht. Die Modellarchitektur von PyAnnote basiert auf rekurrenten neuronalen Netzen (RNNs), die speziell für die Erkennung von Sprachmustern trainiert wurden.

2. **Sprachtranskription mit Whisper**: Whisper ist ein auf Transformer-Modellen basierendes System, das von OpenAI entwickelt wurde. Es kann sowohl die Erkennung als auch die Transkription von Sprache durchführen. Die Transkription erfolgt dabei durch die Anwendung eines Encoder-Decoders, der auf große Mengen an gesprochener Sprache trainiert wurde. Whisper ist in der Lage, auch in multilingualen Kontexten präzise Transkriptionen zu erstellen.

3. **NLP-Zusammenfassung mit OpenAI und HuggingFace**: Um eine Zusammenfassung des Meetings zu erstellen, wird der generierte Prompt an OpenAI's GPT-Modell oder HuggingFace-Modelle übergeben. Diese Transformer-Modelle analysieren den bereitgestellten Prompt und erstellen eine konsistente, strukturierte Zusammenfassung. Transformer-Modelle sind aufgrund ihrer Selbstaufmerksamkeitsmechanismen besonders gut darin, den Kontext der Daten zu verstehen und Zusammenfassungen zu erstellen.

Die technische Architektur kombiniert moderne Methoden des maschinellen Lernens und nutzt deren Leistungsfähigkeit zur Automatisierung komplexer Audioanalysen.

## Technische Dokumentation für Entwickler

Das Projekt besteht aus mehreren wichtigen Komponenten, die im Folgenden beschrieben werden:

### 1. Backend (Flask)

Das Backend ist in Python mit Flask entwickelt und verfügt über mehrere API-Endpunkte zur Verarbeitung von Audiodateien:

- **/upload**: Akzeptiert Audiodateien im MP3- oder WAV-Format und speichert sie im Upload-Verzeichnis. MP3-Dateien werden dabei automatisch nach WAV konvertiert.
- **/analyze**: Führt die Sprecherdiarisierung und Transkription durch. Es wird die Pipeline von PyAnnote und das Whisper-Modell verwendet, um die einzelnen Sprecher zu identifizieren und deren Beiträge zu transkribieren.
- **/generate\_summary**: Nimmt die analysierten Segmente und erstellt mithilfe von GPT- oder HuggingFace-Modellen eine strukturierte Zusammenfassung.

### 2. Frontend (HTML + JavaScript)

Das Frontend ist eine einfache Benutzeroberfläche, die es dem Benutzer ermöglicht, Audiodateien hochzuladen und zu analysieren.

- **Upload-Formular**: Ein Formular, das es dem Benutzer ermöglicht, Audiodateien hochzuladen.
- **Audioplayer**: Der Player ist in Wavesurfer.js eingebettet und stellt die Wellenform der hochgeladenen Audiodatei dar. Benutzer können hier einzelne Segmente abspielen, die im Analyseprozess identifiziert wurden.
- **Analyse- und Zusammenfassungsfunktionen**: Es gibt Schaltflächen zur Ausführung der Diarisierung, zur Vorschau des Prompts sowie zur Generierung der Zusammenfassung.

### 3. Modelle (NLP-Integration)

In der Datei `models.py` sind die verfügbaren Modelle definiert:

- **Bart-large-cnn (HuggingFace)**: Ein Transformer-Modell, das sich gut zur Zusammenfassung eignet.
- **GPT-4o (OpenAI)**: Ein leistungsstarkes Sprachmodell von OpenAI, das zur Textgenerierung und -zusammenfassung verwendet wird.

### 4. Prompterstellung

Die Prompts werden auf Grundlage der transkribierten Segmente generiert und können anschließend zur Zusammenfassung des Meetings verwendet werden. Dies geschieht in der Datei `meeting-to-protocol.py` und ermöglicht eine strukturierte Ausgabe der Meeting-Inhalte.

## Erweiterungsmöglichkeiten

- **Automatische Protokollerstellung**: Weitergehende Integration von NLP-Modellen zur Verbesserung der Automatisierung von Meeting-Zusammenfassungen.
- **Live-Transkription**: Echtzeit-Sprechererkennung und Transkription während eines Meetings.
- **Bessere Visualisierung**: Verbesserte visuelle Darstellung von Sprecherwechseln und interaktiven Zeitlinien.

## Beitrag zum Projekt

Das Projekt wird derzeit als Prototyp entwickelt, und wir laden interessierte Entwickler ein, an der weiteren Verbesserung und Erweiterung dieser Anwendung mitzuwirken. Das Ziel ist es, die Effizienz von Meeting-Zusammenfassungen zu steigern und die Anwendung so benutzerfreundlich wie möglich zu gestalten.

Wenn du Interesse hast, an diesem Projekt mitzuarbeiten oder Ideen zur Verbesserung einbringen möchtest, dann freuen wir uns auf deine Beiträge. Das Repository ist unter folgendem Link verfügbar: [GitHub-Repository](https://github.com/ogerly/pyannote-whisper-integration)

## Lizenz

Das Projekt steht unter der MIT-Lizenz. Bitte überprüfen Sie die `LICENSE`-Datei für weitere Details.

---

Dies sollte die grundlegenden Informationen enthalten, die notwendig sind, um das Projekt zu verstehen und damit zu arbeiten. Viel Erfolg beim Weiterentwickeln der Anwendung! Wenn noch Fragen bestehen oder mehr Funktionen benötigt werden, kannst du uns gerne kontaktieren.

