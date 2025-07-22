#!/usr/bin/env python3
"""
Memory Diagnostics API Endpoints

Provides HTTP API endpoints for real-time memory monitoring and diagnostics.
This module can be used with FastAPI, Flask, or any ASGI/WSGI framework.

Example usage with FastAPI:
    from fastapi import FastAPI
    from claude_pm.api.memory_endpoints import router
    
    app = FastAPI()
    app.include_router(router, prefix="/api/memory")
"""

import asyncio
from datetime import datetime
from typing import Dict, Any, Optional

from ..services.health_monitor import HealthMonitor
from ..services.memory_diagnostics import get_memory_diagnostics


class MemoryAPI:
    """Memory diagnostics API handler."""
    
    def __init__(self):
        self._monitor = None
        self._memory_diag = None
    
    async def _ensure_services(self):
        """Ensure services are initialized."""
        if not self._monitor:
            self._monitor = HealthMonitor()
            await self._monitor.start()
        
        if not self._memory_diag:
            self._memory_diag = get_memory_diagnostics()
            if not self._memory_diag.running:
                await self._memory_diag.start()
    
    async def get_memory_status(self) -> Dict[str, Any]:
        """Get current memory status."""
        await self._ensure_services()
        
        return {
            "timestamp": datetime.now().isoformat(),
            "memory_pressure": self._monitor.is_memory_pressure_detected(),
            "profile": await self._monitor.get_memory_profile(),
            "status": "healthy" if not self._monitor.is_memory_pressure_detected() else "pressure_detected"
        }
    
    async def get_memory_profile(self) -> Dict[str, Any]:
        """Get detailed memory profile."""
        await self._ensure_services()
        return await self._monitor.get_memory_profile()
    
    async def get_memory_diagnostics(self) -> Dict[str, Any]:
        """Get comprehensive memory diagnostics."""
        await self._ensure_services()
        return await self._monitor.get_memory_diagnostics()
    
    async def perform_cleanup(self, force: bool = False) -> Dict[str, Any]:
        """Perform memory cleanup."""
        await self._ensure_services()
        return await self._monitor.perform_memory_cleanup(force=force)
    
    async def get_cache_metrics(self) -> Dict[str, Any]:
        """Get cache-specific metrics."""
        await self._ensure_services()
        
        try:
            from ..services.shared_prompt_cache import SharedPromptCache
            cache = SharedPromptCache.get_instance()
            return {
                "timestamp": datetime.now().isoformat(),
                "metrics": cache.get_metrics(),
                "info": cache.get_cache_info()
            }
        except Exception as e:
            return {
                "timestamp": datetime.now().isoformat(),
                "error": str(e),
                "metrics": None
            }
    
    async def configure_memory(self, threshold_mb: Optional[float] = None, 
                             auto_cleanup: Optional[bool] = None) -> Dict[str, Any]:
        """Configure memory settings."""
        await self._ensure_services()
        
        changes = []
        
        if threshold_mb is not None:
            self._memory_diag.set_memory_threshold(threshold_mb)
            changes.append(f"threshold set to {threshold_mb}MB")
        
        if auto_cleanup is not None:
            self._memory_diag.enable_auto_cleanup(auto_cleanup)
            changes.append(f"auto_cleanup {'enabled' if auto_cleanup else 'disabled'}")
        
        return {
            "timestamp": datetime.now().isoformat(),
            "changes": changes,
            "current_config": {
                "threshold_mb": self._memory_diag.memory_threshold_mb,
                "auto_cleanup": self._memory_diag.enable_auto_cleanup,
                "profile_interval": self._memory_diag.profile_interval
            }
        }
    
    async def close(self):
        """Cleanup resources."""
        if self._monitor and self._monitor.running:
            await self._monitor.stop()
        
        if self._memory_diag and self._memory_diag.running:
            await self._memory_diag.stop()


# FastAPI Router (optional, only loaded if FastAPI is available)
try:
    from fastapi import APIRouter, HTTPException, Query
    from pydantic import BaseModel
    
    class CleanupRequest(BaseModel):
        force: bool = False
    
    class ConfigureRequest(BaseModel):
        threshold_mb: Optional[float] = None
        auto_cleanup: Optional[bool] = None
    
    router = APIRouter(tags=["memory"])
    _api = MemoryAPI()
    
    @router.get("/status")
    async def memory_status():
        """Get current memory status."""
        return await _api.get_memory_status()
    
    @router.get("/profile")
    async def memory_profile():
        """Get detailed memory profile."""
        return await _api.get_memory_profile()
    
    @router.get("/diagnostics")
    async def memory_diagnostics():
        """Get comprehensive memory diagnostics."""
        return await _api.get_memory_diagnostics()
    
    @router.post("/cleanup")
    async def memory_cleanup(request: CleanupRequest):
        """Perform memory cleanup."""
        return await _api.perform_cleanup(force=request.force)
    
    @router.get("/cache/metrics")
    async def cache_metrics():
        """Get cache-specific metrics."""
        return await _api.get_cache_metrics()
    
    @router.post("/configure")
    async def configure_memory(request: ConfigureRequest):
        """Configure memory settings."""
        return await _api.configure_memory(
            threshold_mb=request.threshold_mb,
            auto_cleanup=request.auto_cleanup
        )
    
    @router.on_event("shutdown")
    async def shutdown_event():
        """Cleanup on shutdown."""
        await _api.close()

except ImportError:
    # FastAPI not available, skip router creation
    router = None


# Flask Blueprint (optional, only loaded if Flask is available)
try:
    from flask import Blueprint, jsonify, request
    
    flask_bp = Blueprint('memory_api', __name__)
    _flask_api = MemoryAPI()
    
    @flask_bp.route('/status', methods=['GET'])
    def flask_memory_status():
        """Get current memory status."""
        loop = asyncio.new_event_loop()
        result = loop.run_until_complete(_flask_api.get_memory_status())
        return jsonify(result)
    
    @flask_bp.route('/profile', methods=['GET'])
    def flask_memory_profile():
        """Get detailed memory profile."""
        loop = asyncio.new_event_loop()
        result = loop.run_until_complete(_flask_api.get_memory_profile())
        return jsonify(result)
    
    @flask_bp.route('/cleanup', methods=['POST'])
    def flask_memory_cleanup():
        """Perform memory cleanup."""
        data = request.get_json() or {}
        force = data.get('force', False)
        
        loop = asyncio.new_event_loop()
        result = loop.run_until_complete(_flask_api.perform_cleanup(force=force))
        return jsonify(result)

except ImportError:
    # Flask not available, skip blueprint creation
    flask_bp = None


# Standalone async server (using aiohttp if available)
async def create_memory_diagnostics_app():
    """Create standalone memory diagnostics web app."""
    try:
        from aiohttp import web
        
        api = MemoryAPI()
        
        async def handle_status(request):
            result = await api.get_memory_status()
            return web.json_response(result)
        
        async def handle_profile(request):
            result = await api.get_memory_profile()
            return web.json_response(result)
        
        async def handle_diagnostics(request):
            result = await api.get_memory_diagnostics()
            return web.json_response(result)
        
        async def handle_cleanup(request):
            data = await request.json()
            force = data.get('force', False)
            result = await api.perform_cleanup(force=force)
            return web.json_response(result)
        
        async def handle_cache_metrics(request):
            result = await api.get_cache_metrics()
            return web.json_response(result)
        
        app = web.Application()
        app.router.add_get('/api/memory/status', handle_status)
        app.router.add_get('/api/memory/profile', handle_profile)
        app.router.add_get('/api/memory/diagnostics', handle_diagnostics)
        app.router.add_post('/api/memory/cleanup', handle_cleanup)
        app.router.add_get('/api/memory/cache/metrics', handle_cache_metrics)
        
        return app
        
    except ImportError:
        return None


# Export main API class and optional integrations
__all__ = ['MemoryAPI', 'router', 'flask_bp', 'create_memory_diagnostics_app']