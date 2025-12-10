# Architettura del Sistema - Photo Organizer Pro

## Panoramica
Applicazione desktop Python modulare per l'organizzazione massiva di foto e video. L'architettura è progettata per garantire affidabilità, prestazioni e sicurezza dei dati, disaccoppiando l'interfaccia utente dalla logica di business.

## Componenti Principali

### 1. Core Logic (`src/core/`)
Il cuore dell'applicazione, indipendente dalla GUI.
- **OrganizerEngine**: Controller principale che coordina le fasi di scansione, mappatura ed esecuzione.
- **MetadataExtractor**: Modulo specializzato nell'estrazione robusta di metadati da vari formati (JPG, PNG, HEIC, MP4, MOV, ecc.). Utilizza una gerarchia di strategie (EXIF -> File System -> Fallback).
- **Scanner**: Gestisce la scansione ricorsiva multi-thread delle directory sorgente.
- **ActionExecutor**: Esegue le operazioni fisiche sui file (Copy, Verify, Delete) con controlli di integrità.

### 2. Data Layer (`src/data/`)
Gestione dello stato e della persistenza temporanea.
- **SessionDatabase**: Database SQLite effimero per la memorizzazione della cache dei file scansionati, metadati estratti e stato delle operazioni. Permette query veloci per statistiche e anteprime senza tenere tutto in RAM.
- **LogManager**: Gestore strutturato dei log (JSON) per audit trail completo.

### 3. UI Layer (`src/ui/`)
Interfaccia utente moderna basata su PySide6 (Qt).
- **MainWindow**: Finestra principale che gestisce la navigazione tra le schermate (Wizard pattern).
- **Widgets**: Componenti riutilizzabili per la selezione file, barre di progresso e visualizzazione tabelle.
- **Workers**: QThread separati per mantenere la GUI reattiva durante le operazioni pesanti (Scansione, Copia).

## Flusso dei Dati
1.  **Input**: L'utente seleziona le sorgenti e configura le regole.
2.  **Indexing**: Lo `Scanner` popola il `SessionDatabase` con i percorsi dei file grezzi.
3.  **Analysis**: I worker estraggono i metadati e aggiornano il DB con date e destinazioni calcolate.
4.  **Preview**: La GUI interroga il DB per mostrare l'anteprima e le statistiche.
5.  **Execution**: `ActionExecutor` legge dal DB, esegue la copia, verifica l'hash e aggiorna lo stato.

## Stack Tecnologico
-   **Linguaggio**: Python 3.10+
-   **GUI**: PySide6 (Qt 6)
-   **Database**: SQLite3
-   **Metadati**: Pillow, exifread, hachoir, pymediainfo
-   **Concorrenza**: `concurrent.futures`, `multiprocessing`
-   **Logging**: `structlog` (JSON format)
