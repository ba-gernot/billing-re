-- Supabase Configuration for Billing RE System
-- Run this in Supabase SQL Editor after project setup

-- Enable Row Level Security on all tables
ALTER TABLE operational_orders ENABLE ROW LEVEL SECURITY;
ALTER TABLE service_orders ENABLE ROW LEVEL SECURITY;
ALTER TABLE billing_documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE invoice_documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE customers ENABLE ROW LEVEL SECURITY;
ALTER TABLE container_types ENABLE ROW LEVEL SECURITY;
ALTER TABLE countries ENABLE ROW LEVEL SECURITY;
ALTER TABLE service_rules ENABLE ROW LEVEL SECURITY;
ALTER TABLE weight_class_rules ENABLE ROW LEVEL SECURITY;
ALTER TABLE tax_rules ENABLE ROW LEVEL SECURITY;
ALTER TABLE main_service_prices ENABLE ROW LEVEL SECURITY;
ALTER TABLE additional_service_prices ENABLE ROW LEVEL SECURITY;

-- Create user roles
CREATE TYPE user_role AS ENUM ('SYSTEM_ADMIN', 'BILLING_CLERK', 'RULE_MANAGER', 'READONLY_USER');

-- Create user profiles table
CREATE TABLE user_profiles (
    id UUID REFERENCES auth.users(id) PRIMARY KEY,
    email TEXT,
    role user_role DEFAULT 'READONLY_USER',
    customer_ids UUID[] DEFAULT '{}',
    permissions JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- RLS Policies

-- System admins can access everything
CREATE POLICY "System admins have full access" ON operational_orders
    FOR ALL TO authenticated
    USING (
        EXISTS (
            SELECT 1 FROM user_profiles
            WHERE user_profiles.id = auth.uid()
            AND user_profiles.role = 'SYSTEM_ADMIN'
        )
    );

-- Billing clerks can access orders for their assigned customers
CREATE POLICY "Billing clerks customer access" ON operational_orders
    FOR ALL TO authenticated
    USING (
        EXISTS (
            SELECT 1 FROM user_profiles
            WHERE user_profiles.id = auth.uid()
            AND user_profiles.role = 'BILLING_CLERK'
            AND customer_id = ANY(user_profiles.customer_ids)
        )
    );

-- Rule managers can access rule tables
CREATE POLICY "Rule managers access rules" ON service_rules
    FOR ALL TO authenticated
    USING (
        EXISTS (
            SELECT 1 FROM user_profiles
            WHERE user_profiles.id = auth.uid()
            AND user_profiles.role IN ('RULE_MANAGER', 'SYSTEM_ADMIN')
        )
    );

-- Master data read access for authenticated users
CREATE POLICY "Authenticated read master data" ON container_types
    FOR SELECT TO authenticated
    USING (true);

CREATE POLICY "Authenticated read countries" ON countries
    FOR SELECT TO authenticated
    USING (true);

-- Similar policies for other tables...
-- (Apply similar patterns to service_orders, billing_documents, etc.)

-- Functions for JWT token validation
CREATE OR REPLACE FUNCTION get_user_role()
RETURNS user_role AS $$
BEGIN
    RETURN (
        SELECT role FROM user_profiles
        WHERE id = auth.uid()
    );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to check customer access
CREATE OR REPLACE FUNCTION has_customer_access(customer_uuid UUID)
RETURNS BOOLEAN AS $$
BEGIN
    RETURN EXISTS (
        SELECT 1 FROM user_profiles
        WHERE id = auth.uid()
        AND (
            role = 'SYSTEM_ADMIN'
            OR customer_uuid = ANY(customer_ids)
        )
    );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;