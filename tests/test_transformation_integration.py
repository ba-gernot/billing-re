import pytest
import asyncio
import json
from datetime import datetime
from httpx import AsyncClient
import sys
import os

# Add the services directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '../services/transformation'))

from main import app


class TestTransformationIntegration:
    """Integration tests for transformation service using roadmap examples"""

    @pytest.fixture
    def sample_operational_order(self):
        """Sample order from requirement documents (1_operative_Auftragsdaten.json)"""
        return {
            "Order": {
                "OrderReference": "ORD20250617-00042",
                "Customer": {
                    "Code": "123456",
                    "Name": "Kunde Test"
                },
                "Freightpayer": {
                    "Code": "234567",
                    "Name": "Frachzahler Test"
                },
                "Consignee": {
                    "Code": "345678",
                    "Name": "Empfänger Test"
                },
                "Container": {
                    "Position": "1",
                    "TransportDirection": "Export",
                    "ContainerTypeIsoCode": "22G1",
                    "TareWeight": "2000",
                    "Payload": "21000",
                    "RailService": {
                        "DepartureDate": "2025-07-13T16:25:00",
                        "DepartureTerminal": {
                            "RailwayStationNumber": "80155283"
                        },
                        "DestinationTerminal": {
                            "RailwayStationNumber": "80137943"
                        }
                    },
                    "TruckingServices": [
                        {
                            "SequenceNumber": "1",
                            "Type": "Lieferung",
                            "TruckingCode": "LB",
                            "Waypoints": [
                                {
                                    "SequenceNumber": "1",
                                    "IsMainAdress": "N",
                                    "WayPointType": "Depot",
                                    "TariffPoint": "23456789",
                                    "AdressCode": "0123456789"
                                },
                                {
                                    "SequenceNumber": "2",
                                    "IsMainAdress": "J",
                                    "WayPointType": "Anfahrstelle",
                                    "TariffPoint": "12345678",
                                    "AdressCode": "9876543210",
                                    "DeliveryDate": "2025-07-15T10:00:00"
                                }
                            ]
                        }
                    ],
                    "AdditionalServices": [
                        {
                            "Code": "123"
                        }
                    ],
                    "DangerousGoodFlag": "J"
                }
            }
        }

    @pytest.mark.asyncio
    async def test_health_endpoint(self):
        """Test health endpoint"""
        async with AsyncClient(app=app, base_url="http://test") as ac:
            response = await ac.get("/health")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"
            assert data["service"] == "transformation"

    @pytest.mark.asyncio
    async def test_transformation_roadmap_example(self, sample_operational_order):
        """Test transformation with roadmap example - should produce specific results"""
        async with AsyncClient(app=app, base_url="http://test") as ac:
            response = await ac.post("/transform", json=sample_operational_order)

            # Basic response validation
            assert response.status_code == 200
            data = response.json()

            # Verify response structure
            assert "operational_order_id" in data
            assert "main_service" in data
            assert "trucking_services" in data
            assert "additional_services" in data
            assert "transformation_summary" in data
            assert "processing_time_ms" in data

            # Verify main service transformation
            main_service = data["main_service"]
            assert main_service["service_type"] == "MAIN"
            assert main_service["customer_code"] == "123456"
            assert main_service["freightpayer_code"] == "234567"
            assert main_service["container_type_iso_code"] == "22G1"

            # Verify calculated fields (from roadmap transformation matrix)
            assert main_service["gross_weight"] == 23000  # 2000 + 21000
            assert main_service["length"] == "20"  # 22G1 -> 20ft
            assert main_service["loading_status"] == "beladen"  # payload > 0
            assert main_service["transport_type"] == "KV"  # trucking services exist
            assert main_service["dangerous_goods_flag"] == True  # "J" -> True

            # Verify route information
            assert main_service["departure_station"] == "80155283"
            assert main_service["destination_station"] == "80137943"

            # Verify trucking services
            assert len(data["trucking_services"]) == 1
            trucking_service = data["trucking_services"][0]
            assert trucking_service["service_type"] == "TRUCKING"
            assert trucking_service["trucking_code"] == "LB"
            assert trucking_service["type_of_trip"] == "Zustellung"  # LB -> Zustellung

            # Verify additional services
            assert len(data["additional_services"]) == 1
            additional_service = data["additional_services"][0]
            assert additional_service["service_type"] == "ADDITIONAL"
            assert additional_service["additional_service_code"] == "123"
            assert additional_service["quantity"] == 5  # waiting time units

            # Verify transformation summary
            summary = data["transformation_summary"]
            assert summary["total_services"] == 3  # 1 main + 1 trucking + 1 additional
            assert summary["dangerous_goods"] == True
            assert "weight_category" in summary

    @pytest.mark.asyncio
    async def test_weight_classification(self, sample_operational_order):
        """Test weight classification logic from roadmap"""
        async with AsyncClient(app=app, base_url="http://test") as ac:
            response = await ac.post("/transform", json=sample_operational_order)
            assert response.status_code == 200

            data = response.json()

            # From roadmap: 23000kg + 20ft container = "20B" class
            expected_weight_class = "20B"  # 20ft container over 20 tons
            summary = data["transformation_summary"]

            assert summary["weight_category"] == expected_weight_class

    @pytest.mark.asyncio
    async def test_invalid_order_validation(self):
        """Test validation with invalid order data"""
        invalid_order = {
            "Order": {
                "OrderReference": "INVALID_FORMAT",  # Wrong format
                "Customer": {
                    "Code": "123"  # Too short
                },
                "Container": {
                    "ContainerTypeIsoCode": "INVALID",  # Invalid container type
                    "TareWeight": "50000",  # Outside valid range
                    "Payload": "-1000",  # Negative payload
                    "TransportDirection": "Invalid",  # Invalid direction
                    "DangerousGoodFlag": "X"  # Invalid flag
                }
            }
        }

        async with AsyncClient(app=app, base_url="http://test") as ac:
            response = await ac.post("/transform", json=invalid_order)

            # Should return validation error
            assert response.status_code == 400
            data = response.json()
            assert "error" in data
            assert "VALIDATION_ERROR" in str(data)

    @pytest.mark.asyncio
    async def test_edge_case_weight_boundary(self, sample_operational_order):
        """Test weight boundary conditions"""
        # Test exactly at 20-ton boundary
        order_20tons = sample_operational_order.copy()
        order_20tons["Order"]["Container"]["TareWeight"] = "2000"
        order_20tons["Order"]["Container"]["Payload"] = "18000"  # Total: exactly 20000

        async with AsyncClient(app=app, base_url="http://test") as ac:
            response = await ac.post("/transform", json=order_20tons)
            assert response.status_code == 200

            data = response.json()
            # Should be 20A (≤20 tons)
            assert data["transformation_summary"]["weight_category"] == "20A"

        # Test just over 20-ton boundary
        order_over_20tons = sample_operational_order.copy()
        order_over_20tons["Order"]["Container"]["TareWeight"] = "2000"
        order_over_20tons["Order"]["Container"]["Payload"] = "18001"  # Total: 20001

        async with AsyncClient(app=app, base_url="http://test") as ac:
            response = await ac.post("/transform", json=order_over_20tons)
            assert response.status_code == 200

            data = response.json()
            # Should be 20B (>20 tons)
            assert data["transformation_summary"]["weight_category"] == "20B"


if __name__ == "__main__":
    # Run specific test
    import subprocess
    result = subprocess.run([
        "python", "-m", "pytest", __file__, "-v", "--tb=short"
    ], capture_output=True, text=True)

    print("STDOUT:")
    print(result.stdout)
    print("STDERR:")
    print(result.stderr)
    print(f"Return code: {result.returncode}")