CREATE DATABASE IF NOT EXISTS guild;

USE guild;

CREATE TABLE IF NOT EXISTS users (
    user_id BIGINT NOT NULL,
    social_score INT NOT NULL DEFAULT 0,
    wordle_score INT NOT NULL DEFAULT 0,
    scramble_score INT NOT NULL DEFAULT 0,
    PRIMARY KEY(user_id)
);

CREATE TABLE IF NOT EXISTS messages (
    message_id BIGINT NOT NULL,
    user_id BIGINT NOT NULL,
    message TEXT,
    FOREIGN KEY(user_id) REFERENCES users(user_id),
    PRIMARY KEY(message_id)
);