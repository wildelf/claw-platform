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

export interface Agent {
  id: string
  name: string
  description: string
  skills: string[]
  tools: Tool[]
}

export interface Skill {
  id: string
  name: string
  description: string
  fileCount: number
  files: Record<string, string>
}