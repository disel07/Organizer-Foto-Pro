# Design Interfaccia Utente (GUI)

L'interfaccia è progettata per guidare l'utente attraverso un processo passo-passo (Wizard), riducendo il carico cognitivo e prevenendo errori.

## Stile Visivo
*   **Tema**: Moderno, pulito (Light/Dark mode system-aware).
*   **Framework**: PySide6 (Qt) con fogli di stile QSS per un look professionale.
*   **Palette**: Colori neutri per la struttura, accenti blu per azioni primarie, verde per successo, rosso/arancio per errori/warning.

## Flusso Schermate

### 1. Selezione Sorgenti e Configurazione
Layout verticale diviso in sezioni logiche.
*   **Area Superiore (Input)**:
    *   Widget per aggiunta multipla di cartelle o interi drive (Drag & Drop supportato).
    *   Lista visuale delle sorgenti selezionate con icone (HD, Cartella) e pulsante rimuovi.
*   **Area Centrale (Opzioni)**:
    *   **Modalità Organizzazione**:
        *   Radio Button A: "Cronologica Pura" (es. `2020/08/15/immagine.jpg`)
        *   Radio Button B: "Per Tipo Media" (es. `Foto/2020/Agosto/` e `Video/2020/...`)
    *   **Destinazione**: Selettore cartella di output. Label con spazio libero disponibile.
*   **Area Inferiore (Azione)**:
    *   Pulsante "Analizza File" (Disabilitato finché non sono selezionate sorgente e destinazione).

### 2. Dashboard di Analisi e Anteprima
Compare dopo la scansione.
*   **Sommario**: Card con statistiche (Totale File, Foto, Video, Dimensione Totale, Duplicati stimati).
*   **Griglia Dati (Table View)**:
    *   Colonne: Anteprima (Thumb), Nome Originale, Data Rilevata, Percorso Destinazione Proposto, Stato.
    *   Possibilità di ordinare e filtrare.
    *   Click destro per aprire file o modificare data manualmente (override).
*   **Pannello Problemi (Collapsible)**:
    *   Lista file "Unknown Date" o corrotti. Opzioni rapide: "Sposta in cartella Unknown", "Ignora", "Usa data file".
*   **Footer**:
    *   Pulsante "Indietro" (Modifica selezione).
    *   Pulsante "Avvia Organizzazione" (Verde, ben visibile).

### 3. Esecuzione e Progresso
Schermata modale o dedicata durante il lavoro.
*   **Progress Bar Principale**: Avanzamento totale (File X di Y).
*   **Progress Bar Secondaria**: Avanzamento file corrente (utile per video grandi).
*   **Log Console**: Finestra di testo scorrevole con log in tempo reale.
    *   Color coding: Info (Grigio), Successo (Verde), Warning (Giallo), Errore (Rosso).
    *   Toggle "Mostra solo errori".
*   **Controlli**: Pulsanti "Pausa" e "Stop di Emergenza".

### 4. Riepilogo Finale
*   Messaggio grande di esito (Successo/Parziale).
*   Statistiche finali: File copiati, Errori, Tempo trascorso.
*   Pulsante "Apri cartella destinazione".
*   Pulsante "Visualizza Log Completo" (apre file .json/.log).
