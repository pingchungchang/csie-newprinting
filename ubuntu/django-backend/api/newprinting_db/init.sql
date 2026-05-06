CREATE TABLE np_balance (
    id SERIAL PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    balance INTEGER NOT NULL DEFAULT 500 CHECK (balance >= 0)
);
