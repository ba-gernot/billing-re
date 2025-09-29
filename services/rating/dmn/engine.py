"""
DMN Engine for dynamic rule execution using pyDMNrules
Provides caching and rule management capabilities
"""

import os
import json
import time
from typing import Dict, Any, Optional, List
from pathlib import Path
import logging

logger = logging.getLogger(__name__)
import redis

try:
    import pyDMNrules
except ImportError:
    pyDMNrules = None
    logger.warning("pyDMNrules not available - DMN functionality will be disabled")

# Import our custom XLSX processor as fallback
try:
    from ...xlsx_dmn_processor import XLSXDMNProcessor
except ImportError:
    try:
        from xlsx_dmn_processor import XLSXDMNProcessor
    except ImportError:
        XLSXDMNProcessor = None
        logger.warning("XLSX DMN processor not available")


class BillingDMNEngine:
    """
    DMN Engine wrapper for the billing system using pyDMNrules
    Handles rule loading, caching, and execution
    """

    def __init__(self, redis_client: Optional[redis.Redis] = None, cache_ttl: int = 300):
        self.cache_ttl = cache_ttl  # 5 minutes default
        self.redis_client = redis_client
        self._engines: Dict[str, Any] = {}  # pyDMNrules.DMN instances
        self._last_modified: Dict[str, float] = {}

        # DMN file paths - now supports both Excel and XML
        self.dmn_base_path = Path(__file__).parent.parent.parent.parent / "shared" / "dmn-rules"

        # Initialize XLSX processor as fallback
        self.xlsx_processor = None
        if XLSXDMNProcessor:
            try:
                self.xlsx_processor = XLSXDMNProcessor(self.dmn_base_path)
                logger.info("XLSX DMN processor initialized as fallback")
            except Exception as e:
                logger.warning(f"Failed to initialize XLSX processor: {e}")

        # Check if pyDMNrules is available
        if pyDMNrules is None and self.xlsx_processor is None:
            logger.error("No DMN engine available - DMN functionality disabled")
            self.enabled = False
        else:
            self.enabled = True
            engine_type = "pyDMNrules" if pyDMNrules else "XLSX processor"
            logger.info(f"Initialized DMN Engine with {engine_type}, cache TTL: {cache_ttl}s")

    def _get_cache_key(self, rule_name: str, input_data: Dict[str, Any]) -> str:
        """Generate cache key for a rule and input"""
        input_hash = hash(str(sorted(input_data.items())))
        return f"dmn:rule:{rule_name}:{input_hash}"

    def _get_rule_path(self, rule_name: str) -> Optional[Path]:
        """Get the file path for a DMN rule (supports .dmn.xlsx, .xlsx and .xml)"""
        # Try .dmn.xlsx first (our new pyDMNrules format)
        dmn_excel_path = self.dmn_base_path / f"{rule_name}.dmn.xlsx"
        if dmn_excel_path.exists():
            return dmn_excel_path

        # Try Excel
        excel_path = self.dmn_base_path / f"{rule_name}.xlsx"
        if excel_path.exists():
            return excel_path

        # Fallback to XML
        xml_path = self.dmn_base_path / f"{rule_name}.xml"
        if xml_path.exists():
            return xml_path

        return None

    def _is_rule_modified(self, rule_name: str) -> bool:
        """Check if a rule file has been modified since last load"""
        rule_path = self._get_rule_path(rule_name)

        if not rule_path:
            logger.warning(f"DMN rule file not found: {rule_name}")
            return False

        current_mtime = rule_path.stat().st_mtime
        last_mtime = self._last_modified.get(rule_name, 0)

        return current_mtime > last_mtime

    def _load_dmn_rule(self, rule_name: str) -> Optional[Any]:
        """Load a DMN rule using pyDMNrules"""
        if not self.enabled:
            return None

        rule_path = self._get_rule_path(rule_name)
        if not rule_path:
            logger.error(f"DMN rule file not found: {rule_name}")
            return None

        try:
            # Create DMN instance
            dmn_engine = pyDMNrules.DMN()

            # Load the rule file (returns status dict)
            status = dmn_engine.load(str(rule_path))

            # Check for errors in status
            if isinstance(status, dict) and 'errors' in status:
                logger.error(f"Failed to load DMN rule {rule_name}: {status['errors']}")
                return None
            elif isinstance(status, str) and status != 'DMN Rules loaded successfully':
                logger.error(f"Failed to load DMN rule {rule_name}: {status}")
                return None

            # Update last modified time
            self._last_modified[rule_name] = rule_path.stat().st_mtime

            logger.info(f"Loaded DMN rule: {rule_name} from {rule_path}")
            return dmn_engine

        except Exception as e:
            logger.error(f"Failed to load DMN rule {rule_name}: {e}")
            return None

    def _get_cached_result(self, cache_key: str) -> Optional[Any]:
        """Get cached result from Redis"""
        if not self.redis_client:
            return None

        try:
            cached = self.redis_client.get(cache_key)
            if cached:
                return json.loads(cached)
        except Exception as e:
            logger.warning(f"Failed to get cached result: {e}")

        return None

    def _cache_result(self, cache_key: str, result: Any) -> None:
        """Cache result in Redis"""
        if not self.redis_client:
            return

        try:
            # Only cache serializable results
            serialized = json.dumps(result, default=str)
            self.redis_client.setex(cache_key, self.cache_ttl, serialized)
        except Exception as e:
            logger.warning(f"Failed to cache result: {e}")

    def get_engine(self, rule_name: str, force_reload: bool = False) -> Optional[Any]:
        """
        Get DMN engine for a rule, with automatic reloading if file changed
        """
        if not self.enabled:
            return None

        # Check if we need to reload
        if force_reload or rule_name not in self._engines or self._is_rule_modified(rule_name):
            engine = self._load_dmn_rule(rule_name)
            if engine:
                self._engines[rule_name] = engine
            else:
                return None

        return self._engines.get(rule_name)

    def execute_rule(self, rule_name: str, input_data: Dict[str, Any],
                    use_cache: bool = True) -> Optional[Dict[str, Any]]:
        """
        Execute a DMN rule with the given input data using pyDMNrules or XLSX processor

        Args:
            rule_name: Name of the DMN rule file (without extension)
            input_data: Input data for the rule
            use_cache: Whether to use caching

        Returns:
            Dictionary with decision results or None if failed
        """
        if not self.enabled:
            logger.warning(f"DMN engine disabled - cannot execute rule {rule_name}")
            return None

        # Create cache key
        cache_key = None
        if use_cache:
            cache_key = self._get_cache_key(rule_name, input_data)
            # Try to get cached result
            cached_result = self._get_cached_result(cache_key)
            if cached_result is not None:
                logger.debug(f"Cache hit for rule {rule_name}")
                return cached_result

        # Try pyDMNrules first if available
        if pyDMNrules:
            result = self._execute_with_pydmnrules(rule_name, input_data)
            if result is not None:
                if use_cache and cache_key:
                    self._cache_result(cache_key, result)
                return result

        # Fallback to XLSX processor
        if self.xlsx_processor:
            result = self._execute_with_xlsx_processor(rule_name, input_data)
            if result is not None:
                if use_cache and cache_key:
                    self._cache_result(cache_key, result)
                return result

        logger.error(f"All DMN execution methods failed for rule: {rule_name}")
        return None

    def _execute_with_pydmnrules(self, rule_name: str, input_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Execute rule using pyDMNrules"""
        try:
            # Get DMN engine
            engine = self.get_engine(rule_name)
            if not engine:
                logger.debug(f"Failed to get pyDMNrules engine for rule: {rule_name}")
                return None

            logger.debug(f"Executing DMN rule {rule_name} with pyDMNrules, input: {input_data}")

            # decide() method may return result dict or tuple (varies by version)
            result_data = engine.decide(input_data)

            # Check for errors in various formats
            is_error = False
            if result_data is None:
                is_error = True
            elif isinstance(result_data, tuple):
                # Tuple format: (result_dict, something_else)
                if len(result_data) > 0 and isinstance(result_data[0], dict) and 'errors' in result_data[0]:
                    is_error = True
            elif isinstance(result_data, dict) and 'errors' in result_data:
                is_error = True

            if is_error:
                logger.debug(f"pyDMNrules execution failed for {rule_name}: {result_data}")
                return None

            # Extract actual result from tuple if needed
            if isinstance(result_data, tuple) and len(result_data) > 0:
                result_data = result_data[0]

            logger.debug(f"pyDMNrules execution successful for {rule_name}: {result_data}")
            return result_data

        except Exception as e:
            logger.debug(f"Exception executing with pyDMNrules {rule_name}: {e}")
            return None

    def _execute_with_xlsx_processor(self, rule_name: str, input_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Execute rule using XLSX processor"""
        try:
            logger.debug(f"Executing DMN rule {rule_name} with XLSX processor, input: {input_data}")

            # Map rule names to XLSX processor methods
            result = None

            if rule_name in ["2_Regeln_Fahrttyp", "trip_type", "TripType"]:
                trucking_code = input_data.get('TruckingCode') or input_data.get('truckingCode') or input_data.get('Trucking Code')
                if trucking_code:
                    trip_type = self.xlsx_processor.evaluate_trip_type(trucking_code)
                    if trip_type:
                        result = {"tripType": trip_type, "TypeOfTrip": trip_type}

            elif rule_name in ["4_Regeln_Gewichtsklassen", "weight_classification", "weight_class", "WeightClassification"]:
                container_length = input_data.get('Length') or input_data.get('containerLength') or input_data.get('Laenge')
                gross_weight = input_data.get('GrossWeight') or input_data.get('grossWeight') or input_data.get('Gewicht')
                preisraster = input_data.get('Preisraster') or input_data.get('priceGrid') or 'N'

                if container_length and gross_weight is not None:
                    # Call evaluate_weight_class with gross_weight as float
                    weight_class = self.xlsx_processor.evaluate_weight_class(
                        container_length=str(container_length),
                        gross_weight=float(gross_weight),
                        preisraster=str(preisraster)
                    )
                    if weight_class:
                        result = {"weightClass": weight_class, "WeightClass": weight_class}

            elif rule_name in ["3_Regeln_Leistungsermittlung", "service_determination", "ServiceDetermination"]:
                verkehrsform = input_data.get('TransportType') or input_data.get('transportType') or input_data.get('Verkehrsform') or "Standard"
                gefahrgut = input_data.get('DangerousGood') or input_data.get('dangerousGoods') or input_data.get('Gefahrgut') or False

                services = self.xlsx_processor.evaluate_service_determination(verkehrsform, gefahrgut)
                if services is not None:
                    result = {"serviceValid": len(services) > 0, "services": services, "AdditionalServiceCode": services}

            if result:
                logger.debug(f"XLSX processor execution successful for {rule_name}: {result}")
            else:
                logger.debug(f"XLSX processor execution failed for {rule_name}")

            return result

        except Exception as e:
            logger.debug(f"Exception executing with XLSX processor {rule_name}: {e}")
            return None

    def reload_all_rules(self) -> Dict[str, bool]:
        """Reload all currently loaded rules"""
        if not self.enabled:
            return {}

        results = {}
        for rule_name in list(self._engines.keys()):
            try:
                new_engine = self._load_dmn_rule(rule_name)
                if new_engine:
                    self._engines[rule_name] = new_engine
                    results[rule_name] = True
                    logger.info(f"Successfully reloaded rule: {rule_name}")
                else:
                    results[rule_name] = False
                    logger.warning(f"Failed to reload rule: {rule_name}")
            except Exception as e:
                results[rule_name] = False
                logger.error(f"Error reloading rule {rule_name}: {e}")

        return results

    def get_rule_info(self, rule_name: str) -> Optional[Dict[str, Any]]:
        """Get information about a loaded rule"""
        if not self.enabled:
            return None

        rule_path = self._get_rule_path(rule_name)
        if not rule_path:
            return None

        engine = self._engines.get(rule_name)

        return {
            'name': rule_name,
            'path': str(rule_path),
            'loaded': engine is not None,
            'modified': rule_path.stat().st_mtime,
            'size': rule_path.stat().st_size,
            'format': rule_path.suffix
        }

    def list_available_rules(self) -> List[str]:
        """List all available DMN rule files"""
        if not self.enabled:
            return []

        rules = []
        if self.dmn_base_path.exists():
            # Look for .dmn.xlsx, .xlsx and .xml files
            for pattern in ['*.dmn.xlsx', '*.xlsx', '*.xml']:
                for rule_file in self.dmn_base_path.glob(pattern):
                    # For .dmn.xlsx files, remove the .dmn part from stem
                    rule_name = rule_file.stem
                    if rule_name.endswith('.dmn'):
                        rule_name = rule_name[:-4]

                    if rule_name not in rules:
                        rules.append(rule_name)

        return sorted(rules)

    def health_check(self) -> Dict[str, Any]:
        """Health check for the DMN engine"""
        return {
            'enabled': self.enabled,
            'redis_connected': self.redis_client is not None,
            'loaded_rules': len(self._engines),
            'available_rules': len(self.list_available_rules()),
            'dmn_path_exists': self.dmn_base_path.exists(),
            'pyDMNrules_available': pyDMNrules is not None
        }


# Global instance
_dmn_engine_instance: Optional[BillingDMNEngine] = None


def get_dmn_engine() -> BillingDMNEngine:
    """Get the global DMN engine instance"""
    global _dmn_engine_instance

    if _dmn_engine_instance is None:
        # Try to connect to Redis
        redis_client = None
        try:
            redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
            redis_client = redis.from_url(redis_url, decode_responses=True)
            # Test connection
            redis_client.ping()
            logger.info("Connected to Redis for DMN caching")
        except Exception as e:
            logger.warning(f"Failed to connect to Redis: {e}")
            redis_client = None

        # Get cache TTL from environment
        cache_ttl = int(os.getenv('DMN_CACHE_TTL', '300'))  # 5 minutes default

        _dmn_engine_instance = BillingDMNEngine(
            redis_client=redis_client,
            cache_ttl=cache_ttl
        )

    return _dmn_engine_instance


def reload_dmn_engine() -> BillingDMNEngine:
    """Reload the global DMN engine instance"""
    global _dmn_engine_instance
    _dmn_engine_instance = None
    return get_dmn_engine()