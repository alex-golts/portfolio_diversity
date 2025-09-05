
MARKET_TO_COUNTRY  = {"Developed": ["Australia", "Austria", "Belgium", "Canada", "Denmark", "Finland", "France", "Germany", "Hong Kong", "Ireland", "Israel", "Italy", "Japan", "Netherlands", "New Zealand", "Norway", "Portugal", "Singapore", "Spain", "Sweden", "Switzerland", "United Kingdom", "United States"],
                      "Emerging": ["Brazil", "Chile", "China", "Colombia", "Czech Republic", "Egypt", "Greece", "Hungary", "India", "Indonesia", "South Korea", "Kuwait", "Malaysia", "Mexico", "Peru", "Philippines", "Poland", "Qatar", "Saudi Arabia", "South Africa", "Taiwan", "Thailand", "Turkey", "UAE"]}

COUNTRIES = MARKET_TO_COUNTRY["Developed"] + MARKET_TO_COUNTRY["Emerging"]

# Build country to market mapping
COUNTRY_TO_MARKET = {}
for key, values in MARKET_TO_COUNTRY.items():
    for value in values:
        COUNTRY_TO_MARKET[value] = key

# Market cap distribution
MARKET_CAP_PCT = {'Large': 70, 'Medium': 15, 'Small': 15}

# URL for IMID ETF data
IMID_URL = 'https://www.ssga.com/uk/en_gb/institutional/etfs/funds/spdr-msci-acwi-imi-ucits-etf-spyi-gy'


def build_region_mappings(region_to_country):
    """Build country to region mapping from region to country mapping."""
    country_to_region = {}
    for key, values in region_to_country.items():
        for value in values:
            country_to_region[value] = key
    return country_to_region

def test_world_coverage(portfolio, region_to_country):
    """
    Check that portfolio components fully and without overlaps cover 
    large, medium and small cap stocks of each country within MSCI ACWI IMI.
    """
    cap_coverage = {}
    for sector in portfolio:
        if sector in region_to_country:
            countries = region_to_country[sector]
        elif sector in MARKET_TO_COUNTRY:
            countries = MARKET_TO_COUNTRY[sector]
        elif sector in COUNTRIES:
            countries = [sector]
        else:
            continue
        for country in countries:
            if country not in cap_coverage:
                cap_coverage[country] = sorted(portfolio[sector])
            else:
                cap_coverage[country] = sorted(cap_coverage[country] + portfolio[sector])
    # Check if all values are identical
    if not cap_coverage:
        return False
    cap_coverage_values = list(cap_coverage.values())
    first_value = cap_coverage_values[0]
    for val in cap_coverage_values:
        if val != first_value:
            return False
    return True