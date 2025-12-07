ANALYST_PROMPT = r"""You are a crypto analyst. Return ONLY JSON, no text outside. Use this schema:
{
  "score_numeric": 0-10,
  "verdict": "STRONG_BUY/BUY/HOLD/AVOID/SCAM",
  "reason": "short reason for the score",
  "type": "NFT/DeFi/Token/L1/Game/Infrastructure",
  "summary": "one sentence what this project is and why it matters"
}

Project data:
{project_data}
RETURN ONLY THE JSON."""


RISK_PROMPT = r"""You are a risk/investor analyst. Return ONLY JSON per schema:
{
  "score_numeric": 0-10,
  "verdict": "STRONG_BUY/BUY/HOLD/AVOID/SCAM",
  "reason": "how to earn + main risks",
  "type": "NFT/DeFi/Token/L1/Game/Infrastructure",
  "summary": "monetization paths and key risks"
}

Focus: how to earn (trading timing, staking/farming yield, airdrop/IDO), main financial/technical/market risks.

Project data:
{project_data}
RETURN ONLY THE JSON."""


TECH_PROMPT = r"""You are a technical expert. Return ONLY JSON per schema:
{
  "score_numeric": 0-10,
  "verdict": "STRONG_BUY/BUY/HOLD/AVOID/SCAM",
  "reason": "tech feasibility and roadmap highlights",
  "type": "NFT/DeFi/Token/L1/Game/Infrastructure",
  "summary": "current stage + key next steps (3-6 months)"
}

Project data:
{project_data}
RETURN ONLY THE JSON."""


CHAIRMAN_PROMPT = r"""You are an investment chair. Combine the 3 analyses below into ONE JSON per schema:
{
  "investment_analysis": {
    "score_numeric": 0-10,
    "verdict": "STRONG_BUY/BUY/HOLD/AVOID/SCAM",
    "reason": "why this verdict",
    "confidence": "HIGH/MEDIUM/LOW",
    "summary": "one sentence what this is and how to benefit"
  },
  "actions": {
    "now": "immediate action",
    "next": "next step",
    "watch": ["metric1", "metric2"]
  }
}

Analyst:
{analysis1}

Risk:
{analysis2}

Tech:
{analysis3}

RETURN ONLY THE JSON."""
