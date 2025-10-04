-- Create necessary PostgreSQL extensions for the chatbot application

-- Enable pgvector extension for vector operations
CREATE EXTENSION IF NOT EXISTS vector;

-- Enable UUID extension for UUID generation
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Enable pg_trgm for text similarity search (optional)
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- Create indexes for better performance (will be applied after tables are created)
-- Note: These will be created by the application migrations