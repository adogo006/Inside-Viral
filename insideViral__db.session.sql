
-- @block tabble remover

DROP TABLE words, weights, request_logs
;

-- @block column adder
ALTER TABLE words ADD COLUMN learning_state learningstate NOT NULL DEFAULT 'pending'
;