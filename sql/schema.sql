CREATE TABLE messages (
    content TEXT,

    id BIGINT PRIMARY KEY,
    created_at TIMESTAMP WITHOUT TIME ZONE,

    author_id BIGINT,
    author_tag VARCHAR(1024),
    author_bot BOOLEAN,

    channel_id BIGINT,
    channel_name VARCHAR(1024),

    guild_id BIGINT,
    guild_name VARCHAR(1024)
);
