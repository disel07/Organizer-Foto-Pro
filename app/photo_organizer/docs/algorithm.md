# Algoritmo di Organizzazione e Logica di Business

## Fase 1: Scansione e Analisi (Scanning Phase)
**Obiettivo**: Identificare i file multimediali e determinare la loro datazione originale.

1.  **Walk Ricorsivo Parallelo**:
    *   Utilizzo di `os.scandir` per efficienza.
    *   Filtraggio iniziale per estensione (case-insensitive) e magic bytes (header file) per evitare falsi positivi.
    *   I file validi vengono inseriti in una coda di lavoro.

2.  **Estrazione Data (Strategia a Priorità)**:
    Per ogni file, si tenta di estrarre la data seguendo questo ordine rigoroso:
    *   **Priorità 1 (EXIF Foto)**: Tag `DateTimeOriginal`, `DateTimeDigitized`, `DateTime`.
    *   **Priorità 2 (Metadati Video)**: QuickTime `CreationDate`, `MediaCreateDate`. Parsing via `hachoir` o `pymediainfo`.
    *   **Priorità 3 (Nome File)**: Regex per pattern comuni (es. `IMG_20200101_*.jpg`, `VID-2021-05-20-*.mp4`).
    *   **Priorità 4 (File System)**: Data di modifica (`mtime`) o creazione (`ctime`), scegliendo la più vecchia tra le due per sicurezza.
    *   **Fallback**: Se nessuna data è determinabile, assegnare a cartella "unknown".

3.  **Caching**:
    *   Salvataggio immediato dei metadati (hash parziale, path, data trovata, dimensione) nel DB SQLite.

## Fase 2: Mappatura e Risoluzione Conflitti (Mapping Phase)
**Obiettivo**: Determinare il percorso di destinazione finale per ogni file.

1.  **Calcolo Percorso Destinazione**:
    *   Applicazione della regola scelta dall'utente (es. `Anno/Mese` o `Tipo/Anno/Mese`).
    *   Esempio: `2023/08/` per una foto del 15 Agosto 2023.

2.  **Gestione Collisioni**:
    *   Verifica se il file esiste già nella destinazione (simulazione).
    *   Se esiste un file con lo stesso nome:
        *   Confronto Hash (se disponibile/calcolabile velocemente) o dimensione.
        *   Se identico: Flag come "Duplicato" (opzione per ignorare).
        *   Se diverso: Generazione nuovo nome con suffisso incrementale: `img_001.jpg` -> `img_001_1.jpg` o `img_001_v2.jpg`.

3.  **Verifiche Preliminari**:
    *   Stima spazio totale richiesto vs spazio disponibile su disco destinazione.
    *   Check permessi di scrittura.

## Fase 3: Esecuzione Sicura (Execution Phase)
**Obiettivo**: Spostare i dati garantendo integrità al 100%.

Operazioni eseguite in batch (es. 100 file alla volta) o parallelizzate (IO bound):

1.  **Pre-Copy Check**:
    *   Calcolo Hash MD5/SHA1 completo del file sorgente (`SourceHash`).

2.  **Copia (Copy)**:
    *   Copia del file byte-per-byte (o via `shutil.copy2` preservando metadati).
    *   **IMPORTANTE**: Mai usare `move`. Sempre `copy` -> `verify` -> `delete`.

3.  **Post-Copy Check**:
    *   Calcolo Hash del file destinazione (`DestHash`).
    *   Confronto: `SourceHash == DestHash`.
    *   Se mismatch: ERRORE CRITICO, abort operazione per quel file, log, delete destinazione corrotta.

4.  **Finalizzazione**:
    *   Se Hash OK:
        *   Scrittura entry nel Log JSON (persistente).
        *   (Opzionale/Configurabile) Cancellazione sicura file sorgente.
    *   Aggiornamento UI progress bar.

## Gestione Errori
*   File corrotti in lettura: Skip e log come "Warning".
*   File system sola lettura: Alert immediato e stop.
*   Interruzione improvvisa: Il DB SQLite mantiene lo stato. Al riavvio, il sistema sa quali file sono stati copiati e verificati, evitando duplicati o lavori parziali.
