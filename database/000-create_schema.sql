CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

DROP TABLE IF EXISTS users;

CREATE TABLE users (
    user_id uuid DEFAULT uuid_generate_v4 (),
    mongo_val jsonb,
    username VARCHAR,
    password_hash VARCHAR,
    email VARCHAR,
    scope jsonb,
    PRIMARY KEY (user_id)
);
/*
CREATE TABLE ssh_keys (
    ssh_key_id uuid DEFAULT uuid_generate_v4 (),
    user_id uuid NOT NULL,
    name VARCHAR NOT NULL,
    fingerprint VARCHAR NOT NULL,
    key VARCHAR NOT NULL,
    type VARCHAR NOT NULL,
    added timestamp(0) NOT NULL DEFAULT NOW(),
    last_used timestamp(0),
    PRIMARY KEY (ssh_key_id),
    CONSTRAINT fk_user
      FOREIGN KEY(user_id)
	  REFERENCES users(user_id)
      ON DELETE CASCADE
);

CREATE TABLE schedules (
    schedule_id uuid DEFAULT uuid_generate_v4 (),
    mongo_val jsonb,
    name VARCHAR NOT NULL,
    language_id uuid NOT NULL,
    category VARCHAR NOT NULL,
    periodicity VARCHAR NOT NULL,
    tags VARCHAR[],
    enabled BOOLEAN,
    config jsonb,
    PRIMARY KEY (schedule_id),
    CONSTRAINT fk_language
      FOREIGN KEY(language_id)
	  REFERENCES languages(language_id)
      ON DELETE SET NULL
);

CREATE TABLE languages (
    language_id uuid DEFAULT uuid_generate_v4 (),
    code VARCHAR NOT NULL,
    name_en VARCHAR NOT NULL,
    name_native VARCHAR NOT NULL,
    PRIMARY KEY (language_id)
);

/* Do we really need / use these in schedules or tasks`
CREATE TABLE notifications (
    notification_id uuid DEFAULT uuid_generate_v4 (),
    mailgun VARCHAR[],
    webhook VARCHAR[],
    slack VARCHAR[],
    PRIMARY KEY (notification_id)
)
 */