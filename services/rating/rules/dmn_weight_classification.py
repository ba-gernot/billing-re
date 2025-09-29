"""
Dynamic weight classification using DMN rules
Replaces hardcoded weight classification logic
"""

from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

from dmn import get_dmn_engine


class DMNWeightClassification:
    """
    Weight classification using DMN rules with fallback to hardcoded logic
    """

    def __init__(self):
        self.dmn_engine = get_dmn_engine()

    def classify_weight(self, container_length: str, gross_weight: int,
                       container_type: str = None) -> str:
        """
        Classify container weight using DMN rules

        Args:
            container_length: Container length (e.g., "20", "40")
            gross_weight: Gross weight in kg
            container_type: Optional container type

        Returns:
            Weight class (e.g., "20A", "20B", "40A", "40B")
        """
        # Prepare input data for DMN
        dmn_input = {
            'containerLength': container_length,
            'grossWeight': gross_weight,
            'containerType': container_type or 'STANDARD'
        }

        # Try DMN rule first: 4_Regeln_Gewichtsklassen
        weight_class = self._execute_weight_classification_dmn(dmn_input)

        if not weight_class:
            # Fallback to hardcoded logic
            weight_class = self._fallback_weight_classification(container_length, gross_weight)

        logger.debug(f"Weight classification: {container_length}ft, {gross_weight}kg -> {weight_class}")
        return weight_class

    def _execute_weight_classification_dmn(self, dmn_input: Dict[str, Any]) -> Optional[str]:
        """Execute DMN rule for weight classification"""
        try:
            result = self.dmn_engine.execute_rule(
                rule_name="4_Regeln_Gewichtsklassen",
                input_data=dmn_input,
                use_cache=True
            )

            if result and isinstance(result, dict):
                # Extract weight class from DMN result
                weight_class = None

                if 'weightClass' in result:
                    weight_class = result['weightClass']
                elif 'class' in result:
                    weight_class = result['class']
                elif 'classification' in result:
                    weight_class = result['classification']

                if weight_class:
                    logger.debug(f"DMN weight classification result: {weight_class}")
                    return weight_class

        except Exception as e:
            logger.warning(f"DMN weight classification failed: {e}")

        return None

    def _fallback_weight_classification(self, container_length: str, gross_weight: int) -> str:
        """
        Fallback hardcoded weight classification logic
        Based on the roadmap rules:
        - 20ft: ≤20 tons = 20A, >20 tons = 20B
        - 40ft: ≤25 tons = 40A, >25 tons = 40B
        """
        # Convert weight to tons
        weight_tons = gross_weight / 1000.0

        if container_length == "20":
            return "20A" if weight_tons <= 20 else "20B"
        elif container_length == "40":
            return "40A" if weight_tons <= 25 else "40B"
        else:
            # Unknown container length, default to 20A
            logger.warning(f"Unknown container length: {container_length}, defaulting to 20A")
            return "20A"

    def get_weight_thresholds(self) -> Dict[str, Dict[str, float]]:
        """Get weight classification thresholds"""
        return {
            "20ft": {
                "light_threshold": 20.0,  # tons
                "heavy_class": "20B",
                "light_class": "20A"
            },
            "40ft": {
                "light_threshold": 25.0,  # tons
                "heavy_class": "40B",
                "light_class": "40A"
            }
        }

    def validate_weight_class(self, weight_class: str) -> bool:
        """Validate if weight class is valid"""
        valid_classes = ["20A", "20B", "40A", "40B"]
        return weight_class in valid_classes

    def get_container_info(self, weight_class: str) -> Dict[str, Any]:
        """Get container information based on weight class"""
        container_info = {
            "20A": {
                "length": "20",
                "category": "light",
                "max_weight_tons": 20,
                "typical_tare_weight": 2000
            },
            "20B": {
                "length": "20",
                "category": "heavy",
                "max_weight_tons": float('inf'),
                "typical_tare_weight": 2000
            },
            "40A": {
                "length": "40",
                "category": "light",
                "max_weight_tons": 25,
                "typical_tare_weight": 3500
            },
            "40B": {
                "length": "40",
                "category": "heavy",
                "max_weight_tons": float('inf'),
                "typical_tare_weight": 3500
            }
        }

        return container_info.get(weight_class, {})

    def classify_multiple_containers(self, containers: list) -> list:
        """
        Classify multiple containers at once

        Args:
            containers: List of container dicts with 'length', 'gross_weight' keys

        Returns:
            List of containers with added 'weight_class' field
        """
        classified_containers = []

        for container in containers:
            container_length = container.get('length', '20')
            gross_weight = container.get('gross_weight', 0)
            container_type = container.get('type', 'STANDARD')

            weight_class = self.classify_weight(
                container_length=container_length,
                gross_weight=gross_weight,
                container_type=container_type
            )

            # Add weight class to container data
            classified_container = container.copy()
            classified_container['weight_class'] = weight_class
            classified_containers.append(classified_container)

        return classified_containers

    def reload_rules(self) -> Dict[str, bool]:
        """Reload weight classification DMN rules"""
        return self.dmn_engine.reload_all_rules()

    def get_rule_status(self) -> Dict[str, Any]:
        """Get status of weight classification DMN rule"""
        rule_info = self.dmn_engine.get_rule_info("4_Regeln_Gewichtsklassen")
        return {
            'rule_name': '4_Regeln_Gewichtsklassen',
            'available': rule_info is not None,
            'loaded': rule_info.get('loaded', False) if rule_info else False,
            'last_modified': rule_info.get('modified') if rule_info else None,
            'fallback_enabled': True
        }