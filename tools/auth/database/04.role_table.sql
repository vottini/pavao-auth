
CREATE TABLE IF NOT EXISTS pavao."role" (
  id              INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
  code            TEXT NOT NULL UNIQUE,
  name            TEXT NOT NULL UNIQUE,
  description     TEXT
);

