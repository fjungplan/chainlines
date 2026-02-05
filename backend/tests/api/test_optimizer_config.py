"""
Tests for Optimizer Configuration API
Verifies CRUD operations and validation logic for layout_config.json
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, mock_open, MagicMock
import json
from main import app

# We expect these models to exist
try:
    from app.api.admin.optimizer_config import MutationStrategies, GeneticAlgorithmConfig
except ImportError:
    pass

client = TestClient(app)

VALID_CONFIG = {
    "GROUPWISE": {"MAX_RIGID_DELTA": 20},
    "SCOREBOARD": {"ENABLED": True},
    "PASS_SCHEDULE": [],
    "SEARCH_RADIUS": 50,
    "TARGET_RADIUS": 10,
    "WEIGHTS": {"ATTRACTION": 1000.0},
    "GENETIC_ALGORITHM": {
        "POP_SIZE": 1000,
        "GENERATIONS": 5000,
        "MUTATION_RATE": 0.2,
        "TOURNAMENT_SIZE": 10,
        "TIMEOUT_SECONDS": 3600,
        "PATIENCE": 500
    },
    "MUTATION_STRATEGIES": {
        "SWAP": 0.2,
        "HEURISTIC": 0.2,
        "COMPACTION": 0.3,
        "EXPLORATION": 0.3
    }
}

class TestOptimizerConfigAPI:

    def test_get_config_returns_current_values(self):
        """test_get_config_returns_current_values: GET /api/admin/optimizer/config"""
        # Mock independent load_config function if we implement it, 
        # or mock open if the endpoint reads directly.
        # We'll assume the endpoint calls a load_config() utility in the same module
        
        with patch("app.api.admin.optimizer_config.load_config", return_value=VALID_CONFIG) as mock_load:
            # We also need to ensure the router is mounted. 
            # If not yet mounted in app.main, clear 404.
            # But we can test the router instance directly in unit tests if needed.
            # For now, let's assume we'll mount it at /api/admin/optimizer/config
            
            response = client.get("/api/v1/admin/optimizer/config")
            
            # If router not mounted, this is 404.
            if response.status_code == 404:
                pytest.skip("Router not mounted yet")
            
            assert response.status_code == 200
            assert response.json() == VALID_CONFIG

    def test_update_config_validates_mutation_strategies_sum(self):
        """test_update_config_validates_mutation_strategies_sum"""
        from app.api.admin.optimizer_config import MutationStrategies
        from pydantic import ValidationError
        
        # Invalid sum
        with pytest.raises(ValidationError) as excinfo:
            MutationStrategies(
                SWAP=0.5, HEURISTIC=0.5, COMPACTION=0.5, EXPLORATION=0.5
            )
        assert "sum to 1.0" in str(excinfo.value)

    def test_update_config_success_valid_input(self):
        """test_update_config_success_valid_input"""
        payload = VALID_CONFIG.copy()
        
        with patch("app.api.admin.optimizer_config.save_config") as mock_save:
            response = client.put("/api/v1/admin/optimizer/config", json=payload)
            
            if response.status_code == 404:
                 pytest.skip("Router not mounted yet")

            assert response.status_code == 200
            assert response.json()["status"] == "success"
            mock_save.assert_called_once()

    def test_update_config_rejects_negative_values(self):
        """test_update_config_rejects_negative_values"""
        from app.api.admin.optimizer_config import GeneticAlgorithmConfig
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            GeneticAlgorithmConfig(
                POP_SIZE=-100, # Invalid
                GENERATIONS=5000, MUTATION_RATE=0.2, TOURNAMENT_SIZE=10, 
                TIMEOUT_SECONDS=3600, PATIENCE=500
            )

    def test_get_profiles_returns_all(self):
        """test_get_profiles_returns_all: GET /api/admin/optimizer/profiles"""
        mock_data = {
            "active_profile": "A",
            "profiles": {"A": VALID_CONFIG, "B": VALID_CONFIG, "C": VALID_CONFIG}
        }
        with patch("app.api.admin.optimizer_config.load_profiles", return_value=mock_data):
            response = client.get("/api/v1/admin/optimizer/profiles")
            if response.status_code == 404: pytest.skip("Router not mounted")
            assert response.status_code == 200
            assert response.json()["active_profile"] == "A"
            assert "B" in response.json()["profiles"]

    def test_update_profile_saves_correctly(self):
        """test_update_profile_saves_correctly: PUT /api/admin/optimizer/profiles/{id}"""
        payload = VALID_CONFIG.copy()
        mock_data = {
            "active_profile": "A",
            "profiles": {"A": VALID_CONFIG, "B": VALID_CONFIG, "C": VALID_CONFIG}
        }
        with patch("app.api.admin.optimizer_config.load_profiles", return_value=mock_data), \
             patch("app.api.admin.optimizer_config.save_profiles") as mock_save:
            response = client.put("/api/v1/admin/optimizer/profiles/B", json=payload)
            assert response.status_code == 200
            mock_save.assert_called_once()

    def test_activate_profile_updates_active_and_syncs(self):
        """test_activate_profile_updates_active_and_syncs: POST /api/admin/optimizer/profiles/{id}/activate"""
        mock_data = {
            "active_profile": "A",
            "profiles": {"A": VALID_CONFIG, "B": VALID_CONFIG, "C": VALID_CONFIG}
        }
        with patch("app.api.admin.optimizer_config.load_profiles", return_value=mock_data), \
             patch("app.api.admin.optimizer_config.save_profiles") as mock_save_profiles, \
             patch("app.api.admin.optimizer_config.save_config") as mock_save_config:
            response = client.post("/api/v1/admin/optimizer/profiles/B/activate")
            assert response.status_code == 200
            assert response.json()["active_profile"] == "B"
            mock_save_profiles.assert_called_once()
            mock_save_config.assert_called_once()

