SIMPLE_ANALYST_PROMPT = r"""Analyze this crypto project and return ONLY JSON (no text before or after):
{
  "score": 1-10,
  "verdict": "STRONG_BUY/BUY/HOLD/AVOID/SCAM",
  "summary": "one sentence what this is and how it makes money",
  "type": "NFT/DeFi/Token/L1/Game/Infrastructure",
  "monetization": ["way1", "way2"],
  "plan": {
    "stage": "Idea/Testnet/Mainnet/Growing",
    "next_steps": ["step1", "step2"]
  },
  "advice": {
    "action_now": "what to do now",
    "watch_for": ["metric1", "metric2"],
    "exit": "when to exit"
  }
}

Project data:
{project_data}
RETURN ONLY THE JSON ABOVE."""


SIMPLE_RISK_PROMPT = r"""You are risk manager and investor. Return ONLY JSON (no text outside) with the same schema:
{
  "score": 1-10,
  "verdict": "STRONG_BUY/BUY/HOLD/AVOID/SCAM",
  "summary": "what this is + main money idea",
  "type": "NFT/DeFi/Token/L1/Game/Infrastructure",
  "monetization": ["way1", "way2", "way3"],
  "plan": {
    "stage": "Idea/Testnet/Mainnet/Growing",
    "next_steps": ["step1", "step2"]
  },
  "advice": {
    "action_now": "what to do now",
    "watch_for": ["metric1", "metric2"],
    "exit": "when to exit"
  }
}

Focus on: how to earn (trading timing, staking/farming yield, airdrop/IDO), risks (financial/technical/market), and practical steps.

Project data:
{project_data}
RETURN ONLY THE JSON ABOVE."""


SIMPLE_TECH_PROMPT = r"""You are technical expert. Return ONLY JSON (no text outside) with the same schema:
{
  "score": 1-10,
  "verdict": "STRONG_BUY/BUY/HOLD/AVOID/SCAM",
  "summary": "what this is + main tech edge",
  "type": "NFT/DeFi/Token/L1/Game/Infrastructure",
  "monetization": ["way1", "way2"],
  "plan": {
    "stage": "Idea/Testnet/Mainnet/Growing",
    "next_steps": ["step1", "step2"]
  },
  "advice": {
    "action_now": "what to do now",
    "watch_for": ["metric1", "metric2"],
    "exit": "when to exit"
  }
}

Cover current stage, roadmap (3/6/12 months), integrations/possibilities, and implementation hurdles.

Project data:
{project_data}
RETURN ONLY THE JSON ABOVE."""


SIMPLE_CHAIRMAN_PROMPT = r"""You are investment strategist. Combine the 3 analyses below into ONE JSON (same schema) and nothing else:
{
  "score": 1-10,
  "verdict": "STRONG_BUY/BUY/HOLD/AVOID/SCAM",
  "summary": "one sentence what this is and how it makes money",
  "type": "NFT/DeFi/Token/L1/Game/Infrastructure",
  "monetization": ["way1", "way2"],
  "plan": {
    "stage": "Idea/Testnet/Mainnet/Growing",
    "next_steps": ["step1", "step2"]
  },
  "advice": {
    "action_now": "what to do now",
    "watch_for": ["metric1", "metric2"],
    "exit": "when to exit"
  }
}

Analyst:
{analysis1}

Risk:
{analysis2}

Tech:
{analysis3}

Score must be 1-10, verbal verdict: STRONG_BUY/BUY/HOLD/AVOID/SCAM. RETURN ONLY THE JSON ABOVE."""
