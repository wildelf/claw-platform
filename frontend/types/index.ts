export interface User {
  id: string
  username: string
  email: string
}

export interface Tool {
  id: string
  name: string
  description: string
}

export interface FeedbackEvent {
  id: string
  type: string
  content: string
  timestamp: number
}

export type AgentStatus = 'pending' | 'active' | 'paused'

export interface Agent {
  id: string
  name: string
  description: string
  role: string
  goal: string
  backstory: string
  skill_ids: string[]
  tool_ids: string[]
  model_config_id: string | null
  status: AgentStatus
  user_id: string
  created_at: string
  updated_at: string
}

export type SkillStatus = 'pending' | 'trained' | 'evolved' | 'needs_review'

// SkillConfig for atomic configuration (model binding, timeout, rate limits, cache)
export interface SkillConfig {
  model_id: string | null
  timeout_ms: number
  max_retries: number
  rate_limit: {
    requests_per_minute: number
    tokens_per_minute: number
  } | null
  cache_enabled: boolean
  cache_ttl_seconds: number
  priority: 'low' | 'medium' | 'high'
  max_concurrent: number
}

// SkillCost for metering
export interface SkillCost {
  total_invocations: number
  successful_invocations: number
  failed_invocations: number
  total_tokens: number
  total_cost: number
  last_invoked_at: string | null
}

// SkillHealth for health status
export interface SkillHealth {
  status: 'healthy' | 'degraded' | 'unhealthy'
  error_rate: number
  average_latency_ms: number
  last_error: string | null
}

export interface Skill {
  id: string
  name: string
  description: string
  path: string
  status: SkillStatus
  feedback_count: number
  version: number
  metadata: Record<string, any>
  user_id: string
  created_at: string
  updated_at: string
  // Extended fields for enterprise features
  config?: SkillConfig
  cost?: SkillCost
  health?: SkillHealth
  category?: string
  tags?: string[]
  is_published?: boolean
  install_count?: number
  input_schema?: Record<string, any> | null
  output_schema?: Record<string, any> | null
}

export interface ModelConfig {
  id: string
  name: string
  type: 'openai' | 'anthropic' | 'local' | 'deepseek' | 'other'
  model: string
  api_key?: string
  base_url?: string
  config: Record<string, any>
  user_id: string
  created_at: string
  updated_at: string
}
