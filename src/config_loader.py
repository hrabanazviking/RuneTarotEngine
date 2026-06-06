# RuneTarot — Configuration Loader
# Manages application configuration from YAML data files

"""
Configuration management for RuneTarot.
All settings are loaded from data/config.yaml and can be modified at runtime.
User changes are saved to session/config_override.yaml (never modifying base data).
"""

from __future__ import annotations

import yaml
from pathlib import Path
from typing import Any, Optional
from copy import deepcopy

from src.utils import get_data_dir, get_session_dir, safe_get
from src.comprehensive_logging import get_logger

logger = get_logger("config")


class ConfigLoader:
    """
    Manages application configuration.
    
    Loads defaults from data/config.yaml.
    Saves user overrides to session/config_override.yaml.
    Never modifies the original data file.
    """
    
    def __init__(self, data_dir: Optional[Path] = None, session_dir: Optional[Path] = None) -> None:
        self._data_dir = data_dir or get_data_dir()
        self._session_dir = session_dir or get_session_dir()
        self._config: dict = {}
        self._loaded: bool = False
    
    def load_config(self) -> dict:
        """
        Load configuration from data files.
        Merges base config with any user overrides.
        """
        # Load base configuration
        base_config_path = self._data_dir / "config.yaml"
        base_config: dict = {}
        
        try:
            with open(base_config_path, "r", encoding="utf-8") as f:
                base_config = yaml.safe_load(f) or {}
            logger.info(f"Loaded base config from {base_config_path}")
        except FileNotFoundError:
            logger.warning(f"Base config not found at {base_config_path}, using defaults")
            base_config = self._default_config()
        except Exception as e:
            logger.error(f"Error loading base config: {e}")
            base_config = self._default_config()
        
        # Load user overrides (if they exist)
        override_path = self._session_dir / "config_override.yaml"
        override_config: dict = {}
        
        try:
            if override_path.exists():
                with open(override_path, "r", encoding="utf-8") as f:
                    override_config = yaml.safe_load(f) or {}
                logger.info(f"Loaded config overrides from {override_path}")
        except Exception as e:
            logger.warning(f"Error loading config overrides: {e}")
        
        # Deep merge: overrides take precedence
        self._config = self._deep_merge(base_config, override_config)
        self._loaded = True
        
        return self._config
    
    def save_config(self) -> None:
        """
        Save current configuration as user overrides.
        Only saves values that differ from the base config.
        """
        if not self._loaded:
            self.load_config()
        
        # Load base config to determine what's been overridden
        base_config_path = self._data_dir / "config.yaml"
        base_config: dict = {}
        
        try:
            with open(base_config_path, "r", encoding="utf-8") as f:
                base_config = yaml.safe_load(f) or {}
        except Exception:
            pass
        
        # Calculate overrides (only values that differ from base)
        overrides = self._calculate_overrides(base_config, self._config)
        
        # Write overrides
        override_path = self._session_dir / "config_override.yaml"
        self._session_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            with open(override_path, "w", encoding="utf-8") as f:
                yaml.dump(overrides, f, default_flow_style=False, allow_unicode=True)
            logger.info(f"Saved config overrides to {override_path}")
        except Exception as e:
            logger.error(f"Error saving config overrides: {e}")
    
    def get(self, key_path: str, default: Any = None) -> Any:
        """
        Get a configuration value using dot-notation path.
        
        Args:
            key_path: Dot-separated path, e.g., "api.model" or "display.theme"
            default: Default value if key not found
        
        Returns:
            The configuration value, or default if not found.
        """
        if not self._loaded:
            self.load_config()
        
        keys = key_path.split(".")
        current = self._config
        
        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return default
        
        return current
    
    def set(self, key_path: str, value: Any) -> None:
        """
        Set a configuration value using dot-notation path.
        
        Args:
            key_path: Dot-separated path, e.g., "api.api_key"
            value: The value to set
        """
        if not self._loaded:
            self.load_config()
        
        keys = key_path.split(".")
        current = self._config
        
        for key in keys[:-1]:
            if key not in current or not isinstance(current[key], dict):
                current[key] = {}
            current = current[key]
        
        current[keys[-1]] = value
        logger.debug(f"Config set: {key_path} = {value if 'key' not in key_path else '***'}")
    
    def get_api_key(self) -> str:
        """Get the API key (masked in logs)."""
        key = str(self.get("api.api_key", ""))
        if key:
            logger.debug("API key retrieved (value hidden)")
        return key
    
    def set_api_key(self, key: str) -> None:
        """Set the API key and enable AI if key is non-empty."""
        self.set("api.api_key", key)
        self.set("api.ai_enabled", bool(key.strip()))
    
    def get_model(self) -> str:
        """Get the AI model name."""
        return str(self.get("api.model", "anthropic/claude-sonnet-4"))
    
    def is_ai_enabled(self) -> bool:
        """Check if AI features are available (key is set)."""
        return bool(self.get("api.ai_enabled", False)) and bool(self.get_api_key().strip())
    
    def get_config_dict(self) -> dict:
        """Return a copy of the full configuration dictionary."""
        if not self._loaded:
            self.load_config()
        return deepcopy(self._config)
    
    @staticmethod
    def _deep_merge(base: dict, override: dict) -> dict:
        """Deep merge two dictionaries. Override values take precedence."""
        result = deepcopy(base)
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = ConfigLoader._deep_merge(result[key], value)
            else:
                result[key] = deepcopy(value)
        return result
    
    @staticmethod
    def _calculate_overrides(base: dict, current: dict) -> dict:
        """Calculate only the values that differ from the base config."""
        overrides: dict = {}
        
        for key, value in current.items():
            if key not in base:
                overrides[key] = deepcopy(value)
            elif isinstance(value, dict) and isinstance(base.get(key), dict):
                sub_overrides = ConfigLoader._calculate_overrides(base[key], value)
                if sub_overrides:
                    overrides[key] = sub_overrides
            elif value != base.get(key):
                overrides[key] = deepcopy(value)
        
        return overrides
    
    @staticmethod
    def _default_config() -> dict:
        """Fallback default configuration if data files are missing."""
        return {
            "application": {
                "name": "RuneTarot",
                "version": "1.0.0",
            },
            "display": {
                "theme": "hermetic",
                "show_reversals": True,
                "card_style": "unicode",
                "animation": True,
                "color_enabled": True,
            },
            "tarot": {
                "ordering": "golden_dawn",
                "default_spread": "celtic_cross",
                "shuffle_method": "fisher_yates",
                "significator_selection": False,
            },
            "api": {
                "provider": "openrouter",
                "base_url": "https://openrouter.ai/api/v1",
                "model": "anthropic/claude-sonnet-4",
                "api_key": "",
                "max_tokens": 4096,
                "temperature": 0.8,
                "ai_enabled": False,
                "ai_interpretation_depth": "full",
            },
            "session": {
                "save_readings": True,
                "max_history": 100,
                "export_format": "markdown",
            },
            "logging": {
                "level": "WARNING",
                "file": "runetarot.log",
            },
        }
