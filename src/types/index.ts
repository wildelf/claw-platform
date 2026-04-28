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

export type ModelModality = 'text' | 'image-to-text' | 'text-to-image' | 'image-to-image' | 'text-to-video' | 'video'

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
  text_model_config_id: string | null
  image_model_config_id: string | null
  video_model_config_id: string | null
  status: AgentStatus
  user_id: string
  created_at: string
  updated_at: string
}

export type SkillStatus = 'pending' | 'trained' | 'evolved' | 'needs_review'

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
}

export interface ModelConfig {
  id: string
  name: string
  type: 'openai' | 'anthropic' | 'local' | 'deepseek' | 'other'
  model: string
  api_key?: string
  base_url?: string
  config: Record<string, any>
  modality?: ModelModality
  user_id: string
  created_at: string
  updated_at: string
}
