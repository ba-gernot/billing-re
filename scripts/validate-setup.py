#!/usr/bin/env python3
"""
Validate Phase 1 setup completion
Checks directory structure, files, and basic configuration
"""

import os
import json
from pathlib import Path

def check_directory_structure():
    """Check if all required directories exist"""
    required_dirs = [
        "frontend/app",
        "frontend/components",
        "frontend/lib",
        "api-gateway/src/routes",
        "api-gateway/src/middleware",
        "api-gateway/src/orchestration",
        "services/transformation/models",
        "services/transformation/validators",
        "services/transformation/enrichers",
        "services/rating/rules",
        "services/rating/pricing",
        "services/rating/offers",
        "services/billing/aggregation",
        "services/billing/tax",
        "services/billing/generation",
        "database/migrations",
        "database/seeds",
        "shared/dmn-rules",
        "shared/price-tables",
        "tests"
    ]

    print("🔍 Checking directory structure...")
    missing_dirs = []

    for dir_path in required_dirs:
        if not os.path.exists(dir_path):
            missing_dirs.append(dir_path)

    if missing_dirs:
        print(f"❌ Missing directories: {missing_dirs}")
        return False
    else:
        print("✅ All required directories present")
        return True

def check_required_files():
    """Check if key setup files exist"""
    required_files = [
        "docker-compose.yml",
        ".env.example",
        "database/migrations/001_initial.sql",
        "database/seeds/002_master_data.sql",
        "supabase-config.sql",
        "services/transformation/main.py",
        "services/transformation/requirements.txt",
        "services/rating/main.py",
        "services/rating/requirements.txt",
        "services/billing/main.py",
        "services/billing/requirements.txt",
        "api-gateway/package.json",
        "api-gateway/src/server.js",
        "README.md",
        ".gitignore"
    ]

    print("\n🔍 Checking required files...")
    missing_files = []

    for file_path in required_files:
        if not os.path.exists(file_path):
            missing_files.append(file_path)

    if missing_files:
        print(f"❌ Missing files: {missing_files}")
        return False
    else:
        print("✅ All required files present")
        return True

def check_docker_config():
    """Validate Docker configuration"""
    print("\n🔍 Checking Docker configuration...")

    if not os.path.exists("docker-compose.yml"):
        print("❌ docker-compose.yml missing")
        return False

    # Basic content check
    with open("docker-compose.yml", "r") as f:
        content = f.read()
        required_services = ["postgres", "redis", "transformation-service", "rating-service", "billing-service", "api-gateway"]

        missing_services = []
        for service in required_services:
            if service not in content:
                missing_services.append(service)

        if missing_services:
            print(f"❌ Missing services in docker-compose.yml: {missing_services}")
            return False

    print("✅ Docker configuration valid")
    return True

def check_database_schema():
    """Check database schema file"""
    print("\n🔍 Checking database schema...")

    schema_file = "database/migrations/001_initial.sql"
    if not os.path.exists(schema_file):
        print("❌ Database schema file missing")
        return False

    with open(schema_file, "r") as f:
        content = f.read()
        required_tables = [
            "operational_orders",
            "service_orders",
            "billing_documents",
            "invoice_documents",
            "customers",
            "container_types",
            "service_rules",
            "main_service_prices"
        ]

        missing_tables = []
        for table in required_tables:
            if f"CREATE TABLE {table}" not in content:
                missing_tables.append(table)

        if missing_tables:
            print(f"❌ Missing tables in schema: {missing_tables}")
            return False

    print("✅ Database schema complete")
    return True

def check_api_structure():
    """Check API Gateway structure"""
    print("\n🔍 Checking API Gateway structure...")

    package_json = "api-gateway/package.json"
    if not os.path.exists(package_json):
        print("❌ API Gateway package.json missing")
        return False

    # Check if required dependencies are present
    with open(package_json, "r") as f:
        package_data = json.load(f)
        required_deps = ["fastify", "@fastify/cors", "@fastify/jwt", "axios", "zod"]

        dependencies = package_data.get("dependencies", {})
        missing_deps = []

        for dep in required_deps:
            if dep not in dependencies:
                missing_deps.append(dep)

        if missing_deps:
            print(f"❌ Missing API Gateway dependencies: {missing_deps}")
            return False

    print("✅ API Gateway structure valid")
    return True

def main():
    """Run all validation checks"""
    print("🚀 Validating Phase 1 Setup\n")

    checks = [
        check_directory_structure(),
        check_required_files(),
        check_docker_config(),
        check_database_schema(),
        check_api_structure()
    ]

    if all(checks):
        print("\n🎉 Phase 1 setup validation PASSED!")
        print("\nNext steps:")
        print("1. Copy .env.example to .env and configure")
        print("2. Run: docker-compose up -d postgres redis")
        print("3. Initialize database with migrations")
        print("4. Start services and test with sample order")
        return True
    else:
        print("\n❌ Phase 1 setup validation FAILED!")
        print("Please fix the issues above before proceeding.")
        return False

if __name__ == "__main__":
    main()