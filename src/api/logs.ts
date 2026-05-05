import client from './client'

export interface LogEntry {
  id: string
  agent_id: string
  session_id: string
  timestamp: string
  action_type: string
  tool_name: string | null
  input_json: string | null
  output_json: string | null
  decision_context: string | null
  error: string | null
}

export const logsApi = {
  async query(params: {
    agent_id?: string
    session_id?: string
    action_type?: string
    tool_name?: string
    offset?: number
    limit?: number
  }): Promise<LogEntry[]> {
    const { data } = await client.get('/logs', { params })
    return data
  }
}
