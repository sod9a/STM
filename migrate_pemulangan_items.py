"""
Migration: Create pemulangan_items table.
Run once: python migrate_pemulangan_items.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from app import app, db
from models import PemulanganItem

with app.app_context():
    db.create_all()
    print("OK: Table 'pemulangan_items' created (or already exists).")

