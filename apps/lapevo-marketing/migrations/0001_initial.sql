-- Waitlist entries table (email required)
CREATE TABLE IF NOT EXISTS waitlist_entry (
    id TEXT PRIMARY KEY,
    email TEXT NOT NULL UNIQUE,
    source TEXT,
    ip_address TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_waitlist_email ON waitlist_entry(email);
CREATE INDEX IF NOT EXISTS idx_waitlist_created_at ON waitlist_entry(created_at);

-- Feature requests table (email optional)
CREATE TABLE IF NOT EXISTS feature_request (
    id TEXT PRIMARY KEY,
    waitlist_entry_id TEXT,
    email TEXT,
    content TEXT NOT NULL,
    source TEXT,
    ip_address TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (waitlist_entry_id) REFERENCES waitlist_entry(id)
);

CREATE INDEX IF NOT EXISTS idx_feature_request_email ON feature_request(email);
CREATE INDEX IF NOT EXISTS idx_feature_request_created_at ON feature_request(created_at);
