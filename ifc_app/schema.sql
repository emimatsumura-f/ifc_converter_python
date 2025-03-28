DROP TABLE IF EXISTS user;
DROP TABLE IF EXISTS conversion_history;
DROP TABLE IF EXISTS file_uploads;
DROP TABLE IF EXISTS ifc_elements_cache;

CREATE TABLE user (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  username TEXT UNIQUE NOT NULL,
  email TEXT UNIQUE NOT NULL,
  password TEXT NOT NULL
);

CREATE TABLE conversion_history (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL,
  filename TEXT NOT NULL,
  processed_date TIMESTAMP NOT NULL,
  element_count INTEGER NOT NULL DEFAULT 0,
  status TEXT NOT NULL DEFAULT 'processing' CHECK (status IN ('processing', 'completed', 'failed')),
  FOREIGN KEY (user_id) REFERENCES user (id)
);

CREATE TABLE file_uploads (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    upload_id INTEGER NOT NULL,
    filename TEXT NOT NULL,
    file_size INTEGER NOT NULL,
    chunk_size INTEGER NOT NULL,
    chunks_total INTEGER NOT NULL,
    chunks_uploaded INTEGER DEFAULT 0,
    upload_status TEXT NOT NULL CHECK (upload_status IN ('pending', 'uploading', 'processing', 'completed', 'failed')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES user (id),
    FOREIGN KEY (upload_id) REFERENCES conversion_history (id)
);

CREATE TABLE ifc_elements_cache (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    conversion_id INTEGER NOT NULL,
    element_type TEXT NOT NULL,
    element_name TEXT,
    element_description TEXT,
    profile_size TEXT,
    weight TEXT,
    length TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (conversion_id) REFERENCES conversion_history (id)
);