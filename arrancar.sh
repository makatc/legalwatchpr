#!/bin/bash
cd /home/makatc/LegalWatch
source venv/bin/activate

# Aplicar migraciones automáticamente
python manage.py makemigrations
python manage.py migrate

# Ejecutar servicio continuo
python -u manage.py servicio_continuo