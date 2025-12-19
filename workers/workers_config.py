"""Job Configuration Persistence"""

import json
from pathlib import Path
from typing import Dict, List
from datetime import datetime
from src.services.logger import app_logger

# ✅ KORRIGIERT: CONFIG_FILE unter workers/config/
CONFIG_FILE = Path(__file__).parent / 'config' / 'workers_config.json'

class WorkersConfig:
    """Persistiere Job-Konfigurationen in JSON"""
    
    @staticmethod
    def load_jobs() -> List[Dict]:
        """Lade Job-Konfiguration aus File"""
        if not CONFIG_FILE.exists():
            # Erste Ausführung: Standard-Jobs zurückgeben
            return WorkersConfig.get_default_jobs()
        
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                jobs = json.load(f)
                return jobs
        except Exception as e:
            app_logger.error(f"Fehler beim Laden der Job-Config: {e}", exc_info=True)
            return WorkersConfig.get_default_jobs()
    
    @staticmethod
    def save_jobs(jobs: List[Dict]) -> bool:
        """Speichere Job-Konfiguration in File"""
        try:
            # ✅ Stelle sicher dass config/ Verzeichnis existiert
            CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
            
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(jobs, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            app_logger.error(f"Fehler beim Speichern der Job-Config: {e}", exc_info=True)
            return False
    
    @staticmethod
    def get_default_jobs() -> List[Dict]:
        """Standard Job-Konfiguration"""
        return [
            {
                'job_type': 'sync_orders',
                'interval_minutes': 15,
                'enabled': True,
                'description': 'Synchronisiere neue Aufträge von TEMU API'
            },
            {
                'job_type': 'sync_inventory',
                'interval_minutes': 5,
                'enabled': True,
                'description': 'Aktualisiere Bestandszahlen'
            },
            {
                'job_type': 'fetch_invoices',
                'interval_minutes': 60,
                'enabled': True,
                'description': 'Hole Rechnungen von TEMU'
            }
        ]
    
    @staticmethod
    def update_job_interval(job_type: str, interval_minutes: int) -> bool:
        """Update Interval für einen Job"""
        jobs = WorkersConfig.load_jobs()
        
        for job in jobs:
            if job['job_type'] == job_type:
                job['interval_minutes'] = interval_minutes
                return WorkersConfig.save_jobs(jobs)
        
        return False
    
    @staticmethod
    def toggle_job(job_type: str, enabled: bool) -> bool:
        """Enable/Disable einen Job"""
        jobs = WorkersConfig.load_jobs()
        
        for job in jobs:
            if job['job_type'] == job_type:
                job['enabled'] = enabled
                return WorkersConfig.save_jobs(jobs)
        
        return False
