#!/bin/bash
cd "$(dirname "$0")"

echo "📸 Avvio Organizer Foto Pro..."

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Errore: Python 3 non trovato!"
    echo "Installa Python 3 per continuare."
    read -p "Premi Invio per uscire..."
    exit 1
fi

# Create Virtual Environment if missing
if [ ! -d "app/venv" ]; then
    echo "⚙️  Configurazione ambiente in corso..."
    python3 -m venv app/venv
    
    echo "📥 Installazione dipendenze..."
    ./app/venv/bin/pip install -r app/photo_organizer/requirements.txt
fi

# Run App
echo "🚀 Lancio applicazione..."
cd app
./venv/bin/python photo_organizer/main.py
