// Create constraints and indexes
CREATE CONSTRAINT company_ticker IF NOT EXISTS
FOR (c:Company) REQUIRE c.ticker IS UNIQUE;

CREATE INDEX company_market IF NOT EXISTS
FOR (c:Company) ON (c.market);

CREATE INDEX company_sector IF NOT EXISTS
FOR (c:Company) ON (c.sector);

// Create seed company - NVIDIA
MERGE (nvda:Company {
    ticker: 'NVDA',
    name: 'NVIDIA Corporation',
    market: 'us',
    sector: 'Technology',
    industry: 'Semiconductors',
    description: 'Designs and manufactures graphics processing units (GPUs)',
    created_at: datetime()
})
ON CREATE SET nvda.created_at = datetime()
ON MATCH SET nvda.updated_at = datetime();

// Create some known related companies
MERGE (amd:Company {ticker: 'AMD', name: 'AMD Corporation', market: 'us', sector: 'Technology'})
MERGE (intc:Company {ticker: 'INTC', name: 'Intel Corporation', market: 'us', sector: 'Technology'})
MERGE (tsm:Company {ticker: 'TSM', name: 'Taiwan Semiconductor', market: 'us', sector: 'Technology'})
MERGE (avgo:Company {ticker: 'AVGO', name: 'Broadcom Inc.', market: 'us', sector: 'Technology'})
MERGE (mrvl:Company {ticker: 'MRVL', name: 'Marvell Technology', market: 'us', sector: 'Technology'})
MERGE (qcom:Company {ticker: 'QCOM', name: 'Qualcomm Inc.', market: 'us', sector: 'Technology'})

// Create relationships
MERGE (nvda)-[:COMPETES_WITH {discovered_at: datetime()}]->(amd)
MERGE (nvda)-[:COMPETES_WITH {discovered_at: datetime()}]->(intc)
MERGE (nvda)-[:PARTNERS_WITH {discovered_at: datetime()}]->(tsm)
MERGE (nvda)-[:PARTNERS_WITH {discovered_at: datetime()}]->(avgo)
MERGE (amd)-[:COMPETES_WITH {discovered_at: datetime()}]->(intc)
MERGE (mrvl)-[:COMPETES_WITH {discovered_at: datetime()}]->(nvda)
MERGE (qcom)-[:PARTNERS_WITH {discovered_at: datetime()}]->(nvda);
