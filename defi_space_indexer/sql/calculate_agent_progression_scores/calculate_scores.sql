-- Optional SQL script for agent progression score calculations
-- This script can be used for additional database-level optimizations
-- or complex scoring calculations that are more efficient in SQL

-- Example: Create a view for quick score lookups
CREATE OR REPLACE VIEW agent_score_summary AS
SELECT 
    a.address as agent_address,
    a.session_address,
    a.agent_index,
    COALESCE(sc.total_score, 0) as total_score,
    COALESCE(sc.resource_balance_score, 0) as resource_balance_score,
    COALESCE(sc.lp_position_score, 0) as lp_position_score,
    COALESCE(sc.farming_score, 0) as farming_score,
    sc.last_calculated_at,
    
FROM agent a
LEFT JOIN agent_score sc ON a.address = sc.agent_address AND a.session_address = sc.session_address;

-- Example: Create an index for better performance on score queries
CREATE INDEX IF NOT EXISTS idx_agent_score_session_total 
ON agent_score (session_address, total_score DESC);

-- Example: Create an index for agent address lookups
CREATE INDEX IF NOT EXISTS idx_agent_score_agent_address 
ON agent_score (agent_address);

-- Example: Create an index for the unique constraint
CREATE INDEX IF NOT EXISTS idx_agent_score_unique 
ON agent_score (agent_address, session_address); 