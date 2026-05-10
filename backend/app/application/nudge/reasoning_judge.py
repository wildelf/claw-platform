import json
import logging
from dataclasses import dataclass
from typing import Literal

logger = logging.getLogger(__name__)


@dataclass
class NudgeDecision:
    should_nudge: bool
    nudge_type: Literal["memory", "skill", "both"]
    priority: Literal["high", "medium", "low"]
    summary: str


class ReasoningJudge:
    """LLM 推理判断层：最终判断是否需要 nudge"""

    SYSTEM_PROMPT = """你是一个记忆决策专家。判断以下 Agent 推理过程是否包含值得持久化的信息。

判断标准：
1. 包含环境配置或技术发现？→ memory
2. 包含用户偏好或沟通习惯？→ memory
3. 包含可复用的执行模式？→ skill
4. 包含重要的错误教训？→ memory
5. 复杂任务（5+工具调用）可以抽象成技能？→ skill

输出 JSON：
{
  "should_nudge": true/false,
  "nudge_type": "memory" | "skill" | "both",
  "priority": "high" | "medium" | "low",
  "summary": "一句话总结"
}"""

    USER_PROMPT = """Agent 推理：
{reasoning}

用户输入：{user_input}

Agent 回复：{agent_output}"""

    def __init__(self):
        self._client = None

    def _get_client(self):
        if self._client is None:
            from langchain_openai import ChatOpenAI
            from app.config import settings
            self._client = ChatOpenAI(
                model=settings.models.default.model,
                api_key=settings.models.default.api_key,
                base_url=settings.models.default.base_url,
            )
        return self._client

    async def judge(
        self,
        reasoning: str,
        user_input: str,
        agent_output: str,
    ) -> NudgeDecision:
        """判断是否触发 nudge"""
        try:
            client = self._get_client()
            user_prompt = self.USER_PROMPT.format(
                reasoning=reasoning,
                user_input=user_input,
                agent_output=agent_output,
            )

            response = await client.ainvoke(
                [{"role": "system", "content": self.SYSTEM_PROMPT},
                 {"role": "user", "content": user_prompt}]
            )

            content = response.content.strip()
            # 尝试解析 JSON
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
            result = json.loads(content)

            return NudgeDecision(
                should_nudge=result.get("should_nudge", False),
                nudge_type=result.get("nudge_type", "memory"),
                priority=result.get("priority", "medium"),
                summary=result.get("summary", ""),
            )
        except Exception as e:
            logger.error(f"ReasoningJudge failed: {e}")
            return NudgeDecision(
                should_nudge=False,
                nudge_type="memory",
                priority="low",
                summary="",
            )