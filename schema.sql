-- USERS TABLE
CREATE TABLE users (
    user_id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100),
    role VARCHAR(20) CHECK (role IN ('PI', 'Admin', 'Finance')) NOT NULL,
    password VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- AWARDS TABLE
CREATE TABLE awards (
    award_id SERIAL PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    sponsor VARCHAR(100),
    start_date DATE,
    end_date DATE,
    total_budget DECIMAL(12,2),
    pi_id INT REFERENCES users(user_id)
);

-- BUDGET_LINES TABLE
CREATE TABLE budget_lines (
    line_id SERIAL PRIMARY KEY,
    award_id INT REFERENCES awards(award_id),
    category VARCHAR(100),
    allocated_amount DECIMAL(12,2),
    spent_amount DECIMAL(12,2) DEFAULT 0.00
);

-- TRANSACTIONS TABLE
CREATE TABLE transactions (
    transaction_id SERIAL PRIMARY KEY,
    award_id INT REFERENCES awards(award_id),
    user_id INT REFERENCES users(user_id),
    category VARCHAR(100),
    description TEXT,
    amount DECIMAL(12,2),
    date_submitted DATE,
    status VARCHAR(20) DEFAULT 'Pending' CHECK (status IN ('Pending', 'Approved', 'Declined'))
);

-- POLICIES TABLE
CREATE TABLE policies (
    policy_id SERIAL PRIMARY KEY,
    policy_level VARCHAR(20) CHECK (policy_level IN ('University', 'Federal', 'Sponsor')) NOT NULL,
    source_name VARCHAR(100),
    policy_text TEXT
);

-- LLM_RESPONSES TABLE
CREATE TABLE llm_responses (
    response_id SERIAL PRIMARY KEY,
    transaction_id INT REFERENCES transactions(transaction_id),
    llm_decision VARCHAR(30) CHECK (llm_decision IN ('Allow', 'Allow with Prior Approval', 'Disallow')),
    reason TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
