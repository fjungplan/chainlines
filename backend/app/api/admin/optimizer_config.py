from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field, field_validator, model_validator
from typing import List, Dict, Any, Optional
import json
import os
import shutil
import time
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

# Paths
BACKEND_CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "optimizer", "layout_config.json")
# Assuming standard structure: backend/app/api/admin/optimizer_config.py -> backend/app/optimizer/layout_config.json
# Wait: __file__ = app/api/admin/optimizer_config.py
# parent 1 = admin
# parent 2 = api
# parent 3 = app
# path = app/optimizer/layout_config.json
# Yes, dirname(dirname(dirname(file))) gives 'app', then join 'optimizer'.

# Frontend Path: We need to traverse up to project root
# backend/app/api/admin/ -> backend/ -> root/
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
# file: backend/app/api/admin/opt_conf.py
# 1: admin
# 2: api
# 3: app
# 4: backend
# 5: chainlines (root)
FRONTEND_CONFIG_PATH = os.path.join(PROJECT_ROOT, "frontend", "src", "utils", "layout", "layout_config.json")

# --- Pydantic Models ---

class MutationStrategies(BaseModel):
    SWAP: float = Field(ge=0.0, le=1.0)
    HEURISTIC: float = Field(ge=0.0, le=1.0)
    COMPACTION: float = Field(ge=0.0, le=1.0)
    EXPLORATION: float = Field(ge=0.0, le=1.0)

    @model_validator(mode='after')
    def check_sum_is_one(self):
        total = self.SWAP + self.HEURISTIC + self.COMPACTION + self.EXPLORATION
        # Allow small float error
        if not (0.99 <= total <= 1.01):
            raise ValueError(f"Mutation strategies must sum to 1.0 (got {total:.2f})")
        return self

class GeneticAlgorithmConfig(BaseModel):
    POP_SIZE: int = Field(gt=0)
    GENERATIONS: int = Field(gt=0)
    MUTATION_RATE: float = Field(ge=0.0, le=1.0)
    TOURNAMENT_SIZE: int = Field(gt=0)
    TIMEOUT_SECONDS: int = Field(gt=0)
    PATIENCE: int = Field(gt=0)

class PassStrategy(BaseModel):
    strategies: List[str]
    iterations: int = Field(gt=0)
    minFamilySize: int = Field(ge=0, alias="min_family_size")
    minLinks: int = Field(ge=0, alias="min_links")
    
    class Config:
        populate_by_name = True  # Allow both camelCase and snake_case

class LayoutConfig(BaseModel):
    GROUPWISE: Dict[str, Any]
    SCOREBOARD: Dict[str, Any]
    PASS_SCHEDULE: List[PassStrategy]
    SEARCH_RADIUS: int = Field(gt=0)
    TARGET_RADIUS: int = Field(gt=0)
    WEIGHTS: Dict[str, float]
    GENETIC_ALGORITHM: GeneticAlgorithmConfig
    MUTATION_STRATEGIES: MutationStrategies

# --- Helpers ---

def load_config() -> dict:
    if not os.path.exists(BACKEND_CONFIG_PATH):
        raise HTTPException(status_code=500, detail="Backend config file not found")
    with open(BACKEND_CONFIG_PATH, "r") as f:
        return json.load(f)

def save_config(config: dict):
    """Save config with atomic write and sync to frontend."""
    import tempfile
    
    # 1. Update Backend Config
    success = False
    last_error = None
    
    try:
        # Write to temporary file first
        temp_fd, temp_path = tempfile.mkstemp(dir=os.path.dirname(BACKEND_CONFIG_PATH), suffix='.json')
        try:
            with os.fdopen(temp_fd, 'w') as f:
                json.dump(config, f, indent=4)
            
            # Use retry loop for atomic rename (Docker/Bind-mount resilience)
            for i in range(5):
                try:
                    os.replace(temp_path, BACKEND_CONFIG_PATH)
                    success = True
                    break
                except OSError as e:
                    last_error = e
                    time.sleep(0.1)
            
            if not success:
                # Fallback to direct write if rename fails (e.g. Device busy)
                logger.warning(f"Atomic rename failed, falling back to direct write: {last_error}")
                with open(BACKEND_CONFIG_PATH, "w") as f:
                    json.dump(config, f, indent=4)
                success = True
                
            logger.info(f"Configuration saved successfully to {BACKEND_CONFIG_PATH}")
            
            # 2. Sync to Frontend (if path exists)
            if success and os.path.exists(os.path.dirname(FRONTEND_CONFIG_PATH)):
                shutil.copy2(BACKEND_CONFIG_PATH, FRONTEND_CONFIG_PATH)
                logger.info(f"Configuration synced to {FRONTEND_CONFIG_PATH}")
                
        finally:
            # Clean up temp file if it still exists
            if os.path.exists(temp_path):
                try:
                    os.unlink(temp_path)
                except:
                    pass
    except Exception as e:
        logger.error(f"Failed to save config: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# --- Endpoints ---

@router.get("/config")
def get_config():
    """Get current layout configuration."""
    return load_config()

@router.put("/config")
def update_config(config: LayoutConfig):
    """Update layout configuration with validation."""
    # Validate pass schedule logic (optional extra checks)
    for strategy in config.PASS_SCHEDULE:
        if "HYBRID" in strategy.strategies and len(strategy.strategies) > 1:
            raise HTTPException(status_code=422, detail="HYBRID strategy must be exclusive")

    save_config(config.model_dump())
    return {"status": "success", "message": "Configuration updated"}

@router.post("/config/reset")
def reset_config():
    """Reset configuration to defaults (Not fully implemented yet)."""
    # TODO: Define ALL defaults here or load from a defaults file
    return {"status": "error", "message": "Not implemented"}
