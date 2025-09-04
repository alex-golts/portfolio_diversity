"""
The goal of this script is to determine the appropriate weights for the 
following 8 non overlapping sectors to create a portfolio that ultimately 
tracks the global equity investment market, as reflected by the 
MSCI All Country World Index Investable Market Index (ACWI IMI):
1. United States - Large/Mid cap
2. Developed Europe - Large/Mid cap
3. Emerging markets - All cap
4. Developed World - Small cap
5. Japan - Large/Mid cap
6. Developed Pacific ex Japan - Large/Mid cap
7. Canada - Large/Mid cap
8. Israel - Large/Mid cap

It extracts individual country weights in the MSCI ACWI IMI index from the 
web page of the IMID ETF that tracks this index. then it calculates the 
appropriate weights for the above 8 sectors after appropriate grouping.

Q: Why not just buy IMID and that's it?
A: Sometimes it's not feasible to have one's whole assets invested into 
    a single ETF. for example, In Israel, the only passive index option 
    currently available in pension funds is S&P 500. But one may still want
    their entire equity assets (pension, private brokerage etc'.) to collectively
    track a diversified world index. 
    Another reasons may include flexibility and reduction of overall expense ratio. 

Q: Why specifically these 8 sectors?
A: I chose them manually for a number of reasons:
    - There is no "World ex US" ETF that is accumulating and domiciled outside of US
        (thus, doesn't expose non US citizens to draconian inheritance tax) as far as I know.
    - They have no overlaps and fully cover the global equity investment market.
    - They reflect choices based on existing ETFs that are large, cheap and 
        track complementary MSCI based indexes (and not mix with FTSE, to avoid overlaps).
"""

IMID_url = 'https://www.ssga.com/uk/en_gb/institutional/etfs/funds/spdr-msci-acwi-imi-ucits-etf-spyi-gy'

import requests
from bs4 import BeautifulSoup
import json
import pandas as pd
from constants import *
from utils import read_input
import argparse

def world_coverage(portfolio, country_weights):
    # check that the portfolio components fully and without overlaps cover 
    # large, medium and small cap stocks of each country within MSCI ACWI IMI.
    cap_coverage = {}
    pct_coverage = {}
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
                pct_coverage[country] = sum([(country_weights[country]/100.0)*MARKET_CAP_PCT[cap] for cap in portfolio[sector]])
            else:
                cap_coverage[country] = sorted(cap_coverage[country] + portfolio[sector])
                pct_coverage[country] += sum([(country_weights[country]/100.0)*MARKET_CAP_PCT[cap] for cap in portfolio[sector]])
    
    # check overlap and coverage:
    overlapping_caps = {}
    missing_caps = {}
    overlapping_pct = {}
    missing_pct = {}

    all_caps = list(MARKET_CAP_PCT.keys())
    for country,weight in country_weights.items():
        if country not in cap_coverage:
            cap_coverage[country] = []
        missing_caps_cur = [element for element in all_caps if element not in cap_coverage[country]]
        if missing_caps_cur:
            missing_caps[country] = missing_caps_cur
            missing_pct[country] = sum([(country_weights[country]/100.0)*MARKET_CAP_PCT[cap] for cap in missing_caps_cur])
        
        extra_caps_cur = []
        for element in all_caps:
            if cap_coverage[country].count(element)>1:
                extra_caps_cur.append(element)
        if extra_caps_cur:
            overlapping_caps[country] = extra_caps_cur
            overlapping_pct[country] = sum([(country_weights[country]/100.0)*MARKET_CAP_PCT[cap] for cap in extra_caps_cur])
    results = {}
    results['country_weights'] = country_weights
    results['missing_caps'] = missing_caps
    results['missing_pct'] = missing_pct
    results['overlapping_caps'] = overlapping_caps
    results['overlapping_pct'] = overlapping_pct

    return results

def print_report(results, portfolio_df):
    missing_caps = results['missing_caps']
    missing_pct = results['missing_pct']
    overlapping_caps = results['overlapping_caps']
    overlapping_pct = results['overlapping_pct']
    if not missing_caps and not overlapping_caps:
        print(f"Total market coverage={portfolio_df['Weight'].sum()}. No overlaps or missing segments.")
    if missing_caps:
        print(f"Missing segments: {missing_caps}")
        print(f"Missing coverage: {missing_pct}")
        print(f"Total market coverage={portfolio_df['Weight'].sum()}, Total missed coverage: {sum(missing_pct.values())}")
    if overlapping_caps:
        print(f"Overlapping segments: {overlapping_caps}")
        print(f"Overlapping coverage: {overlapping_pct}")
        print(f"Total market coverage={portfolio_df['Weight'].sum()}, Total overlapping coverage: {sum(overlapping_pct.values())}")

def main(file_path):
    portfolio = read_input(file_path)

    response = requests.get(IMID_url)
    html_content = response.text
    soup = BeautifulSoup(html_content, "html.parser")
    json_input = soup.find("input", id="fund-geographical-breakdown")

    json_data = json.loads(json_input["value"])
    table_data = json_data.get("attrArray", [])
    df = pd.DataFrame(columns=["Country", "Weight", "Market", "Region"])
    df["Country"] = [item['name']['value'] for item in table_data]
    df["Weight"] = [float(item['weight']['value'][:-1]) for item in table_data]

    missing_countries = set(COUNTRIES) - set(df['Country'])
    # "smallest" economy countries that are in MSCI Emerging IMI but missing from IMID currently:
    for country in missing_countries:
        df.loc[len(df)] = {'Country': country, 'Weight': 0.00}
    df["Market"] = df["Country"].map(COUNTRY_TO_MARKET)
    df["Region"] = df["Country"].map(COUNTRY_TO_REGION)
    df.loc[df["Region"].isnull(), "Region"] = df.loc[df["Region"].isnull(), "Country"]
    
    region_weights = df.groupby("Region")["Weight"].sum()
    region_weights = region_weights.sort_values(ascending=False)

    market_weights = df.groupby("Market")["Weight"].sum()
    market_weights = market_weights.sort_values(ascending=False)

    print("Region Weights:")
    print(region_weights)

    print("Market Weights:")
    print(market_weights)

    portfolio_df = pd.DataFrame(columns=["Sector", "Market Caps", "Weight"])
    # calculate portfolio weights
    sector_weights = []

    for sector, caps in portfolio.items():
        cap_pct =  sum([MARKET_CAP_PCT[cap] for cap in caps])
        if sector in region_weights.index:
            sector_weight = region_weights[sector]*(cap_pct/100.0)
        elif sector in market_weights.index:
            sector_weight = market_weights[sector]*(cap_pct/100.0)
        sector_weights.append(sector_weight)
    portfolio_df['Sector'] = list(portfolio.keys())
    portfolio_df['Market Caps'] = list(portfolio.values())
    portfolio_df['Weight'] = sector_weights

    print(portfolio_df)

    country_weights = df.set_index('Country')['Weight'].to_dict()
    results = world_coverage(portfolio, country_weights)
    print_report(results, portfolio_df)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Read portfolio elements from YAML file")
    parser.add_argument('--file', type=str, help="Path to the YAML input file", default="portfolios/perfect_with_SNP500.yaml")
    args = parser.parse_args()
    main(args.file)

