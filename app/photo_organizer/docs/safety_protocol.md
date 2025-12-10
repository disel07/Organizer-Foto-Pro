# Protocollo di Sicurezza Dati

La sicurezza e l'integrità dei dati utente sono la priorità assoluta. Questo documento definisce le regole inderogabili implementate nel codice.

## 1. Principio "Non-Distruttivo" (Read-Only Source)
*   **Regola**: L'applicazione non deve MAI modificare i file sorgente durante le fasi di analisi o copia.
*   **Implementazione**: Le cartelle sorgente sono aperte in modalità sola lettura dove possibile. L'operazione di default è sempre `COPY`, mai `MOVE`.
*   **Cancellazione**: La cancellazione dei file originali avviene (se opzione attivata) SOLO dopo che la copia è stata verificata tramite hash.

## 2. Verifica Integrità (Hash Check)
*   Ogni trasferimento file è validato crittograficamente.
*   **Algoritmo**: MD5 (bilanciamento velocità/collisioni accettabile per media) o SHA-256 (se performance consentono).
*   **Procedura**:
    1.  Read Source -> Update HashContext -> Write Dest -> Update HashContext.
    2.  Al termine, rileggere Destinazione (o usare buffer scrittura) per calcolare Hash finale.
    3.  Se `Hash(Source) != Hash(Dest)` -> **ALLARM**. Cancellare destinazione, loggare errore, NON toccare sorgente.

## 3. Prevenzione Sovrascrittura (Anti-Collision)
*   Prima di scrivere qualsiasi file, si verifica l'esistenza di un file con lo stesso nome nel path target.
*   Nessun file viene mai sovrascritto silenziosamente.
*   **Strategia**: Rename automatico con pattern predicibile (`_1`, `_2`, ecc.) o skip se contenuto identico (deduplica sicura basata su hash).

## 4. Gestione Errori e Atomic operations
*   L'aggiornamento del Log JSON e lo stato nel DB avvengono solo a operazione conclusa.
*   Intercettazione eccezioni OS (Disk Full, Permission Denied, Path Too Long).
*   In caso di "Disk Full": Pausa immediata del processo, alert utente, possibilità di resume dopo pulizia o cambio destinazione (se architettura lo permette).

## 5. Log e Audit Trail
*   Viene generato un file di log strutturato (JSON Lines) immutabile per sessione.
*   Ogni entry contiene: Timestamp, SourcePath, DestPath, FileSize, HashSource, HashDest, Status.
*   Questo log serve come "ricevuta" dell'operazione e permette script di rollback o verifica esterna.

## 6. Validazione Input
*   Controllo esistenza e leggibilità path sorgente.
*   Controllo scrivibilità path destinazione.
*   Filtro file di sistema o nascosti (`.DS_Store`, `Thumbs.db`) per evitare inquinamento destinazione.
