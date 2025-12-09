"""Job Models für Scheduler"""

from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from enum import Enum

class JobType(str, Enum):
    SYNC_ORDERS = "sync_orders"
    SYNC_INVENTORY = "sync_inventory"
    FETCH_INVOICES = "fetch_invoices"
    FULL_WORKFLOW = "full_workflow"

class JobStatusEnum(str, Enum):
    IDLE = "IDLE"
    RUNNING = "RUNNING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"

class JobSchedule(BaseModel):
    """Job-Schedule Konfiguration"""
    interval_minutes: int
    enabled: bool = True
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None
    last_status: JobStatusEnum = JobStatusEnum.IDLE
    last_error: Optional[str] = None
    last_duration_seconds: Optional[float] = None

class JobConfig(BaseModel):
    """Job-Konfiguration"""
    job_type: JobType
    schedule: JobSchedule
    description: str

class JobStatusResponse(BaseModel):
    """Job-Status für Dashboard"""
    job_id: str
    config: JobConfig
    status: dict
    recent_logs: List[str] = []
