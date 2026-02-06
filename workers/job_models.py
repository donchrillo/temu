"""Job Models - Datenstrukturen für Job-Konfiguration"""

from enum import Enum
from pydantic import BaseModel
from typing import Optional

class JobType(str, Enum):
    """Verfügbare Job-Typen"""
    SYNC_ORDERS = "sync_orders"
    SYNC_INVENTORY = "sync_inventory"

class JobStatusEnum(str, Enum):
    """Job-Status"""
    IDLE = "idle"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"

class JobSchedule(BaseModel):
    """Job-Schedule Konfiguration"""
    interval_minutes: int
    enabled: bool = True

class JobConfig(BaseModel):
    """Komplette Job-Konfiguration"""
    job_type: JobType
    schedule: JobSchedule
    description: str
