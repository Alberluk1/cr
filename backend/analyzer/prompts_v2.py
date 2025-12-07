"""Более контекстные промпты, но с жёстким требованием вернуть только число 1-10."""

EXPERIENCED_PROJECT_PROMPT = """Analyze this crypto project and return ONLY a number 1-10.

PROJECT: {name}
DESCRIPTION: {description}
SOURCE: {source}
CATEGORY: {category}

SCORING HINTS:
- 9-10: Revolutionary, strong team, working product
- 7-8: Innovative, good potential, early stage
- 5-6: Average, needs monitoring
- 3-4: Risky, weak fundamentals
- 1-2: Likely scam

Return ONLY a single number 1-10. Nothing else."""


DEFI_PROJECT_PROMPT = """Score this DeFi project 1-10. Return ONLY a number 1-10.

NAME: {name}
DESCRIPTION: {description}
TVL: {tvl}
AUDIT: {audit_status}

- 10: Blue-chip (Uniswap/Aave level)
- 8-9: Strong innovation, good TVL
- 6-7: Promising but risky
- 4-5: Copycat, low TVL
- 1-3: High risk, possible scam

Number 1-10:"""


NFT_PROJECT_PROMPT = """Evaluate this NFT project 1-10. Return ONLY a number 1-10.

COLLECTION: {name}
DESCRIPTION: {description}
ARTIST: {artist}
UTILITY: {utility}

- 10: Legendary artist, strong community
- 8-9: Good art, active community
- 6-7: Average, depends on execution
- 4-5: Low effort, cash grab
- 1-3: Likely rug pull

Number 1-10:"""


GENERIC_PROMPT = """Score this crypto project 1-10. Return ONLY a number 1-10.

PROJECT: {name}
DESCRIPTION: {description}
SOURCE: {source}
CATEGORY: {category}

- 9-10: Strong team/product
- 7-8: Good potential
- 5-6: Average
- 3-4: Risky
- 1-2: Likely scam

Number 1-10:"""
