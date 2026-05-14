import sys
import os
from app import app, db
from models import SoftwareLicense, SoftwareUser

def seed_software():
    with app.app_context():
        # Create the new tables
        db.create_all()
        
        # Initial software list
        softwares = [
            {
                "name": "Adobe Acrobat",
                "description": "Perisian untuk membaca dan menyunting fail PDF.",
                "icon_class": "bi-file-earmark-pdf",
                "bg_color": "rgba(220,53,69,0.1)",
                "text_color": "#dc3545",
                "total_licenses": 10
            },
            {
                "name": "Adobe Creative Cloud",
                "description": "Suite aplikasi kreatif termasuk Photoshop dan Illustrator.",
                "icon_class": "bi-palette",
                "bg_color": "rgba(214,51,132,0.1)",
                "text_color": "#d63384",
                "total_licenses": 5
            },
            {
                "name": "Microsoft Visio",
                "description": "Aplikasi rajah dan grafik vektor untuk perniagaan.",
                "icon_class": "bi-diagram-3",
                "bg_color": "rgba(56,145,220,0.1)",
                "text_color": "#3891dc",
                "total_licenses": 10
            },
            {
                "name": "Microsoft Project",
                "description": "Perisian pengurusan projek dan jadual tugas.",
                "icon_class": "bi-kanban",
                "bg_color": "rgba(25,135,84,0.1)",
                "text_color": "#198754",
                "total_licenses": 10
            },
            {
                "name": "Dewan Eja11",
                "description": "Alat penyemak ejaan dan tatabahasa Bahasa Melayu.",
                "icon_class": "bi-spellcheck",
                "bg_color": "rgba(102,16,242,0.1)",
                "text_color": "#6610f2",
                "total_licenses": 20
            }
        ]
        
        for s in softwares:
            existing = SoftwareLicense.query.filter_by(name=s["name"]).first()
            if not existing:
                new_software = SoftwareLicense(**s)
                db.session.add(new_software)
                print(f"Added {s['name']}")
            else:
                print(f"Already exists: {s['name']}")
                
        db.session.commit()
        print("Done seeding software.")

if __name__ == '__main__':
    seed_software()
