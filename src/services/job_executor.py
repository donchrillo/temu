"""
Unified Job Executor Service
Single source of truth for all job executions
Used by: API, Scheduler (if needed in future)
"""

import asyncio
import time
from enum import Enum
from typing import Dict, Any, Optional
from datetime import datetime

from src.modules.temu.order_workflow_service import OrderWorkflowService
from src.modules.temu.inventory_workflow_service import InventoryWorkflowService
from src.services.log_service import log_service
from src.services.logger import app_logger


class JobType(str, Enum):
    """Available job types"""
    SYNC_ORDERS = "sync_orders"
    SYNC_INVENTORY = "sync_inventory"
    FETCH_INVOICES = "fetch_invoices"


class JobExecutor:
    """
    Central executor for all job runs.
    
    This is the ONLY place where jobs are executed, regardless of source:
    - API endpoint (/api/jobs/{id}/run-now)
    - Future: Scheduler/Timer
    - Future: Webhooks
    
    Benefits:
    - Single source of truth
    - Consistent logging and error handling
    - Easy to extend with new job types
    - Centralized performance monitoring
    """
    
    def __init__(self):
        self.order_service = OrderWorkflowService()
        self.inventory_service = InventoryWorkflowService()
    
    async def execute(
        self,
        job_id: str,
        job_type: JobType,
        parent_order_status: int = 2,
        days_back: int = 7,
        verbose: bool = False,
        log_to_db: bool = True,
        mode: str = "quick",
    ) -> Dict[str, Any]:
        """
        Execute a job synchronously.
        
        Args:
            job_id: Unique identifier for this job run
            job_type: Type of job to execute
            parent_order_status: Status code for order sync (2-5)
            days_back: Days to look back for data
            verbose: Enable verbose logging
            log_to_db: Log results to database
            mode: Execution mode (for inventory: 'quick' or 'full')
        
        Returns:
            {
                "success": bool,
                "job_id": str,
                "job_type": str,
                "result": Any,
                "duration_seconds": float,
                "started_at": str (ISO),
                "finished_at": str (ISO),
                "error": str (optional)
            }
        
        Raises:
            ValueError: For unknown job types
        """
        start_time = datetime.now()
        started_timestamp = start_time.isoformat()
        
        try:
            app_logger.info(f"🚀 Job started: {job_id} (type={job_type})")
            
            if job_type == JobType.SYNC_ORDERS:
                success = await self._execute_sync_orders(
                    job_id=job_id,
                    parent_order_status=parent_order_status,
                    days_back=days_back,
                    verbose=verbose,
                    log_to_db=log_to_db,
                )
            
            elif job_type == JobType.SYNC_INVENTORY:
                success = await self._execute_sync_inventory(
                    job_id=job_id,
                    verbose=verbose,
                    log_to_db=log_to_db,
                    mode=mode,
                )
            
            elif job_type == JobType.FETCH_INVOICES:
                success = await self._execute_fetch_invoices(job_id=job_id)
            
            else:
                raise ValueError(f"Unknown job type: {job_type}")
            
            duration = (datetime.now() - start_time).total_seconds()
            
            return {
                "success": success,
                "job_id": job_id,
                "job_type": job_type.value,
                "duration_seconds": duration,
                "started_at": started_timestamp,
                "finished_at": datetime.now().isoformat(),
            }
        
        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()
            error_msg = str(e)
            
            app_logger.error(
                f"❌ Job failed: {job_id} - {error_msg}",
                exc_info=True
            )
            
            return {
                "success": False,
                "job_id": job_id,
                "job_type": job_type.value,
                "duration_seconds": duration,
                "started_at": started_timestamp,
                "finished_at": datetime.now().isoformat(),
                "error": error_msg,
            }
    
    async def _execute_sync_orders(
        self,
        job_id: str,
        parent_order_status: int,
        days_back: int,
        verbose: bool,
        log_to_db: bool,
    ) -> bool:
        """Execute order sync workflow"""
        # Validate parameters
        valid_status = [2, 3, 4, 5]
        if parent_order_status not in valid_status:
            raise ValueError(f"Invalid order status: {parent_order_status}")
        
        if days_back < 1:
            raise ValueError("Days must be >= 1")
        
        # Start job logging
        if log_to_db:
            log_service.start_job_capture(job_id, "sync_orders")
        
        try:
            app_logger.info(
                f"📦 Order Sync: status={parent_order_status}, days={days_back}"
            )
            
            # Run the workflow
            result = await self._async_wrapper(
                self.order_service.run_complete_workflow,
                parent_order_status=parent_order_status,
                days_back=days_back,
                verbose=verbose,
            )
            
            if log_to_db:
                log_service.end_job_capture(success=True)
            
            return result
        
        except Exception as e:
            if log_to_db:
                log_service.end_job_capture(success=False)
            raise
    
    async def _execute_sync_inventory(
        self,
        job_id: str,
        verbose: bool,
        log_to_db: bool,
        mode: str,
    ) -> bool:
        """Execute inventory sync workflow"""
        if mode not in ["quick", "full"]:
            raise ValueError(f"Invalid mode: {mode}")
        
        # Start job logging
        if log_to_db:
            log_service.start_job_capture(job_id, "sync_inventory")
        
        try:
            app_logger.info(f"📊 Inventory Sync: mode={mode}")
            
            # Run the workflow
            result = await self._async_wrapper(
                self.inventory_service.run_complete_workflow,
                mode=mode,
                verbose=verbose,
            )
            
            if log_to_db:
                log_service.end_job_capture(success=True)
            
            return result
        
        except Exception as e:
            if log_to_db:
                log_service.end_job_capture(success=False)
            raise
    
    async def _execute_fetch_invoices(self, job_id: str) -> bool:
        """Execute fetch invoices workflow"""
        app_logger.info("📄 Fetch Invoices: Not yet implemented")
        # TODO: Implement invoice fetching
        return True
    
    @staticmethod
    async def _async_wrapper(func, *args, **kwargs) -> bool:
        """
        Execute a potentially blocking function in thread pool.
        This allows DB operations to work with async.
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, lambda: func(*args, **kwargs))


# Singleton instance
_executor_instance: Optional[JobExecutor] = None


def get_job_executor() -> JobExecutor:
    """Get or create the JobExecutor singleton"""
    global _executor_instance
    if _executor_instance is None:
        _executor_instance = JobExecutor()
    return _executor_instance
