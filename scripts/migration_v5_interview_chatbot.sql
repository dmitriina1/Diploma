-- Migration v5: Add AI Interview Chatbot tables

-- Create table for interview chat sessions
CREATE TABLE IF NOT EXISTS interview_chat_sessions (
    id SERIAL PRIMARY KEY,
    user_session VARCHAR(255) NOT NULL,
    topic VARCHAR(255) NOT NULL,
    difficulty VARCHAR(20) NOT NULL,
    messages TEXT NOT NULL, -- JSON array of messages
    status VARCHAR(20) NOT NULL DEFAULT 'active', -- 'active', 'completed', 'abandoned'
    summary TEXT, -- Final summary from LLM
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_interview_chat_user ON interview_chat_sessions(user_session);
CREATE INDEX IF NOT EXISTS idx_interview_chat_status ON interview_chat_sessions(status);
CREATE INDEX IF NOT EXISTS idx_interview_chat_created ON interview_chat_sessions(created_at DESC);

-- Add trigger for auto-update updated_at
CREATE OR REPLACE FUNCTION update_interview_chat_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_interview_chat_updated_at ON interview_chat_sessions;
CREATE TRIGGER trigger_interview_chat_updated_at
    BEFORE UPDATE ON interview_chat_sessions
    FOR EACH ROW
    EXECUTE FUNCTION update_interview_chat_updated_at();

COMMENT ON TABLE interview_chat_sessions IS 'AI-powered interview chat sessions with LLM';
