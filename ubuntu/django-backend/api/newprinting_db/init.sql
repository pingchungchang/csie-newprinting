CREATE TABLE np_balance (
    id SERIAL PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    balance INTEGER NOT NULL DEFAULT 500 CHECK (balance >= 0)
);
CREATE TABLE np_admin (
    username TEXT UNIQUE NOT NULL
);
CREATE TABLE np_submission (
    uid SERIAL PRIMARY KEY,
    wid INTEGER,
    username TEXT NOT NULL,
    printer TEXT NOT NULL,
    pages INTEGER,
    money INTEGER,
    retry_count INTEGER NOT NULL DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
