-- PostgreSQL Schema for GrantGuard
-- Converted from MySQL to PostgreSQL syntax

-- Enable UUID extension if needed
-- CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- USERS TABLE
CREATE TABLE IF NOT EXISTS users (
    user_id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE,
    role VARCHAR(20) CHECK (role IN ('PI', 'Admin', 'Finance')) NOT NULL DEFAULT 'PI',
    password VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- AWARDS TABLE
CREATE TABLE IF NOT EXISTS awards (
    award_id SERIAL PRIMARY KEY,
    created_by_email VARCHAR(255),
    title VARCHAR(200) NOT NULL,
    sponsor VARCHAR(100),
    sponsor_type VARCHAR(50),
    amount DECIMAL(15,2),
    start_date DATE,
    end_date DATE,
    status VARCHAR(50) DEFAULT 'Pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    total_budget DECIMAL(12,2),
    pi_id INTEGER,
    department VARCHAR(255),
    college VARCHAR(255),
    contact_email VARCHAR(255),
    abstract TEXT,
    keywords VARCHAR(500),
    collaborators TEXT,
    budget_personnel DECIMAL(15,2),
    budget_equipment DECIMAL(15,2),
    budget_travel DECIMAL(15,2),
    budget_materials DECIMAL(15,2),
    CONSTRAINT awards_pi_id_fkey FOREIGN KEY (pi_id) REFERENCES users(user_id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS awards_pi_id_idx ON awards(pi_id);

-- POLICIES TABLE
CREATE TABLE IF NOT EXISTS policies (
    policy_id SERIAL PRIMARY KEY,
    policy_level VARCHAR(20) CHECK (policy_level IN ('University', 'Federal', 'Sponsor')) NOT NULL,
    source_name VARCHAR(100),
    policy_text TEXT
);

-- TRANSACTIONS TABLE
CREATE TABLE IF NOT EXISTS transactions (
    transaction_id SERIAL PRIMARY KEY,
    award_id INTEGER,
    user_id INTEGER,
    category VARCHAR(100),
    description TEXT,
    amount DECIMAL(12,2),
    date_submitted DATE,
    status VARCHAR(20) CHECK (status IN ('Pending', 'Approved', 'Declined')) DEFAULT 'Pending',
    CONSTRAINT transactions_award_id_fkey FOREIGN KEY (award_id) REFERENCES awards(award_id) ON DELETE CASCADE,
    CONSTRAINT transactions_user_id_fkey FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS transactions_award_id_idx ON transactions(award_id);
CREATE INDEX IF NOT EXISTS transactions_user_id_idx ON transactions(user_id);

-- BUDGET_LINES TABLE
CREATE TABLE IF NOT EXISTS budget_lines (
    line_id SERIAL PRIMARY KEY,
    award_id INTEGER,
    category VARCHAR(100),
    allocated_amount DECIMAL(12,2),
    spent_amount DECIMAL(12,2) DEFAULT 0.00,
    CONSTRAINT budget_lines_award_id_fkey FOREIGN KEY (award_id) REFERENCES awards(award_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS budget_lines_award_id_idx ON budget_lines(award_id);

-- LLM_RESPONSES TABLE
CREATE TABLE IF NOT EXISTS llm_responses (
    response_id SERIAL PRIMARY KEY,
    transaction_id INTEGER,
    llm_decision VARCHAR(30) CHECK (llm_decision IN ('Allow', 'Allow with Prior Approval', 'Disallow')),
    reason TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT llm_responses_transaction_id_fkey FOREIGN KEY (transaction_id) REFERENCES transactions(transaction_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS llm_responses_transaction_id_idx ON llm_responses(transaction_id);

