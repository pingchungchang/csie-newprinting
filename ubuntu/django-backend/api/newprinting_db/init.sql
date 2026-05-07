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
    status TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
