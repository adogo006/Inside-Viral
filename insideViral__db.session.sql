
-- @block tabble remover
TRUNCATE TABLE words RESTART IDENTITY

DROP TABLE words, weights
;

-- @block column adder
ALTER TABLE words ADD COLUMN state_edu processstate NOT NULL DEFAULT 'pending'
;