from utils import read_input

MARKET_TO_COUNTRY  = {"Developed": ["Australia", "Austria", "Belgium", "Canada", "Denmark", "Finland", "France", "Germany", "Hong Kong", "Ireland", "Israel", "Italy", "Japan", "Netherlands", "New Zealand", "Norway", "Portugal", "Singapore", "Spain", "Sweden", "Switzerland", "United Kingdom", "United States"],
                      "Emerging": ["Brazil", "Chile", "China", "Colombia", "Czech Republic", "Egypt", "Greece", "Hungary", "India", "Indonesia", "South Korea", "Kuwait", "Malaysia", "Mexico", "Peru", "Philippines", "Poland", "Qatar", "Saudi Arabia", "South Africa", "Taiwan", "Thailand", "Turkey", "UAE"]}

COUNTRIES = MARKET_TO_COUNTRY["Developed"] + MARKET_TO_COUNTRY["Emerging"]

COUNTRY_TO_MARKET = {}
for key, values in MARKET_TO_COUNTRY.items():
    for value in values:
        if value not in COUNTRY_TO_MARKET:
            COUNTRY_TO_MARKET[value] = []
        COUNTRY_TO_MARKET[value] = key

REGION_TO_COUNTRY = read_input("regions.yaml")
COUNTRY_TO_REGION = {}
for key, values in REGION_TO_COUNTRY.items():
    for value in values:
        if value not in COUNTRY_TO_REGION:
            COUNTRY_TO_REGION[value] = []
        COUNTRY_TO_REGION[value] = key

MARKET_CAP_PCT = {'Large': 70, 'Medium': 15, 'Small': 15}

def test_world_coverage(portfolio):
    # check that the portfolio components fully and without overlaps cover 
    # large, medium and small cap stocks of each country within MSCI ACWI IMI.
    cap_coverage = {}
    for sector in portfolio:
        if sector in REGION_TO_COUNTRY:
            countries = REGION_TO_COUNTRY[sector]
        elif sector in MARKET_TO_COUNTRY:
            countries = MARKET_TO_COUNTRY[sector]
        elif sector in COUNTRIES:
            countries = [sector]
        for country in countries:
            if country not in cap_coverage:
                cap_coverage[country] = sorted(portfolio[sector])
            else:
                cap_coverage[country] = sorted(cap_coverage[country] + portfolio[sector])
    # check if all values are identical
    cap_coverage_values = list(cap_coverage.values())
    first_value = cap_coverage_values[0]
    for val in cap_coverage_values:
        if val!=first_value:
            return False
    return True

    
if __name__ == '__main__':
    portfolio = read_input('portfolios/perfect_with_SNP500.yaml')
    assert(test_world_coverage(portfolio))