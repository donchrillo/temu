"""Base Workflow Service - Shared Infrastructure für TEMU Workflows"""

from datetime import datetime
from typing import Optional

from modules.shared.config.settings import (
    TEMU_APP_KEY, TEMU_APP_SECRET, TEMU_ACCESS_TOKEN, TEMU_API_ENDPOINT,
)
from modules.shared import log_service
from modules.shared.database.repositories.jtl_common.jtl_repository import JtlRepository
from modules.shared.connectors.temu.service import TemuMarketplaceService


class BaseWorkflowService:
    """
    Gemeinsame Infrastruktur für TEMU Workflow-Services.
    
    Bereitgestellt:
    - DB Connection State Management (_toci_conn, _jtl_conn)
    - Cleanup mit Hook für Subklassen
    - Credential-Validierung
    - TemuMarketplaceService Lazy-Loader
    - JtlRepository Lazy-Loader
    - Job-Lifecycle Helpers (ID-Generierung, Duration, Capture)
    """
    
    def __init__(self):
        # Shared Service Cache
        self._temu_service: Optional[TemuMarketplaceService] = None
        
        # Connection State (pro Transaktionsblock gesetzt)
        self._toci_conn = None
        self._jtl_conn = None
        
        # Shared Repo Cache
        self._jtl_repo: Optional[JtlRepository] = None
    
    # ═══════════════════════════════════════════════════════════════
    # Lifecycle Helpers
    # ═══════════════════════════════════════════════════════════════
    
    @staticmethod
    def _generate_job_id(prefix: str) -> str:
        """Erzeugt eine eindeutige Job-ID mit Timestamp."""
        return f"{prefix}_{int(datetime.now().timestamp())}"
    
    @staticmethod
    def _validate_credentials(job_id: str, workflow_name: str) -> bool:
        """Prüft ob TEMU API Credentials gesetzt sind."""
        if not all([TEMU_APP_KEY, TEMU_APP_SECRET, TEMU_ACCESS_TOKEN]):
            log_service.log(job_id, workflow_name, "ERROR", 
                          "✗ TEMU Credentials nicht gesetzt!")
            return False
        return True
    
    # ═══════════════════════════════════════════════════════════════
    # Connection Management
    # ═══════════════════════════════════════════════════════════════
    
    def _cleanup_connections(self):
        """
        Setzt Connection- und Repo-Caches zurück.
        Ruft _cleanup_service_caches() für subklassen-spezifische Caches auf.
        """
        self._toci_conn = None
        self._jtl_conn = None
        self._jtl_repo = None
        self._cleanup_service_caches()
    
    def _cleanup_service_caches(self):
        """
        Hook für Subklassen: Domain-spezifische Repo-/Service-Caches zurücksetzen.
        Override in Subklassen.
        """
        pass
    
    # ═══════════════════════════════════════════════════════════════
    # Shared Lazy Loaders
    # ═══════════════════════════════════════════════════════════════
    
    def _get_temu_service(self, verbose: bool = False) -> TemuMarketplaceService:
        """Lazy-Loader für TemuMarketplaceService (shared zwischen allen Workflows)."""
        if self._temu_service is None:
            self._temu_service = TemuMarketplaceService(
                app_key=TEMU_APP_KEY,
                app_secret=TEMU_APP_SECRET,
                access_token=TEMU_ACCESS_TOKEN,
                endpoint=TEMU_API_ENDPOINT,
                verbose=verbose,
            )
        return self._temu_service
    
    def _get_jtl_repo(self) -> Optional[JtlRepository]:
        """Lazy-Loader für JtlRepository (shared zwischen allen Workflows)."""
        if self._jtl_repo is None and self._jtl_conn:
            self._jtl_repo = JtlRepository(connection=self._jtl_conn)
        return self._jtl_repo
