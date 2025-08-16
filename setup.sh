#!/bin/sh

# Exit immediately if a command exits with a non-zero status.
set -e

pip install .
python src/graphics_db_server/scripts/init_db.py
python src/graphics_db_server/scripts/ingest_data.py
