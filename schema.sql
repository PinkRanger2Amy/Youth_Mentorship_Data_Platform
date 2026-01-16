-- Mentors
CREATE TABLE IF NOT EXISTS mentors (
  mentor_id SERIAL PRIMARY KEY,
  first_name TEXT NOT NULL,
  last_name  TEXT NOT NULL,
  email      TEXT UNIQUE NOT NULL,
  phone      TEXT,
  availability TEXT,
  interests  TEXT,
  created_at TIMESTAMP DEFAULT NOW()
);

-- Sessions (parent table)
CREATE TABLE IF NOT EXISTS sessions (
  session_id SERIAL PRIMARY KEY,
  mentor_id INT REFERENCES mentors(mentor_id),
  session_date DATE NOT NULL,
  topic TEXT,
  created_at TIMESTAMP DEFAULT NOW()
);

-- Session notes (child table)
CREATE TABLE IF NOT EXISTS session_notes (
  note_id SERIAL PRIMARY KEY,
  session_id INT NOT NULL REFERENCES sessions(session_id),
  note TEXT NOT NULL,
  created_at TIMESTAMP DEFAULT NOW()
);

-- Raw mentor intake
CREATE TABLE IF NOT EXISTS mentor_intake_submissions (
  submission_id BIGSERIAL PRIMARY KEY,
  submitted_at TIMESTAMP NOT NULL,
  raw_payload JSONB NOT NULL,
  source TEXT DEFAULT 'online_form'
);
-- Mentees
CREATE TABLE IF NOT EXISTS mentees (
  mentee_id SERIAL PRIMARY KEY,
  first_name TEXT NOT NULL,
  last_name  TEXT NOT NULL,
  guardian_name TEXT,
  guardian_email TEXT,
  phone TEXT,
  school TEXT,
  grade TEXT,
  interests TEXT,
  created_at TIMESTAMP DEFAULT NOW()
);

-- Raw mentee intake
CREATE TABLE IF NOT EXISTS mentee_intake_submissions (
  submission_id BIGSERIAL PRIMARY KEY,
  submitted_at TIMESTAMP NOT NULL,
  raw_payload JSONB NOT NULL,
  source TEXT DEFAULT 'online_form'
);
-- Matches (Mentor ↔ Mentee)
CREATE TABLE IF NOT EXISTS matches (
  match_id BIGSERIAL PRIMARY KEY,
  mentor_id INT NOT NULL REFERENCES mentors(mentor_id) ON DELETE CASCADE,
  mentee_id INT NOT NULL REFERENCES mentees(mentee_id) ON DELETE CASCADE,
  match_score INT NOT NULL DEFAULT 0,
  match_reason TEXT,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW(),
  UNIQUE (mentor_id, mentee_id)
);

