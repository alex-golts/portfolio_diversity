"""
Portfolio Diversity Calculator

Calculate optimal weights for geographic sectors/ETFs to track global equity markets
when direct investment in a world index ETF isn't feasible.

This tool determines appropriate weights for user-defined portfolio sectors to create
a combined portfolio that tracks the MSCI All Country World Index Investable Market 
Index (ACWI IMI) - the most comprehensive global equity benchmark.

COMMON USE CASES:
1. Pension Fund Constraint: Your pension fund only offers S&P 500, but you want global 
   diversification across all your investment accounts.

2. Cost Optimization: Combining multiple lower-cost regional ETFs instead of 
   a single expensive world ETF.

3. Flexibility: Maintaining control over regional allocations while achieving 
   world market exposure.

PORTFOLIO TYPES SUPPORTED:
- Perfect Coverage: 100% global market replication with zero overlaps
- Approximate Coverage: Simplified portfolios covering 85-95% of global markets  
- Custom Combinations: Any mix of countries, regions, and market caps

EXAMPLE OUTPUT:
For a "perfect coverage" portfolio, you might get:
- United States (Large+Medium): 52.3%
- Developed Europe (Large+Medium): 13.8% 
- Emerging Markets (All caps): 11.8%
- Japan (Large+Medium): 5.0%
- etc.

This tells you exactly how to weight each sector/ETF to achieve global market exposure.

RECOMMENDED STARTING POINT:
Use portfolios/perfect_with_SNP500.yaml for comprehensive global coverage.
"""

import requests
from bs4 import BeautifulSoup
import json
import pandas as pd
import argparse
from utils import (
    read_yaml, load_regions, 
    validate_portfolio_sectors, get_countries_for_sector
)

def fetch_country_weights(url, timeout=30):
    """
    Fetch country weights from IMID ETF webpage.
    
    Args:
        url (str): URL to fetch data from
        timeout (int): Request timeout in seconds
        
    Returns:
        pd.DataFrame: DataFrame with Country and Weight columns
        
    Raises:
        Exception: If data fetching or parsing fails
    """
    try:
        print(f"Fetching data from {url}")
        response = requests.get(url, timeout=timeout)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, "html.parser")
        json_input = soup.find("input", id="fund-geographical-breakdown")
        
        if not json_input:
            raise ValueError("Could not find 'fund-geographical-breakdown' element on the webpage. "
                           "The website structure may have changed.")
        
        json_data = json.loads(json_input["value"])
        table_data = json_data.get("attrArray", [])
        
        if not table_data:
            raise ValueError("No country data found in the JSON response")
        
        # Build DataFrame
        df = pd.DataFrame(columns=["Country", "Weight"])
        df["Country"] = [item['name']['value'] for item in table_data]
        df["Weight"] = [float(item['weight']['value'][:-1]) for item in table_data]
        
        print(f"Successfully fetched data for {len(df)} countries")
        return df
        
    except requests.RequestException as e:
        raise Exception(f"Failed to fetch data from {url}: {e}")
    except json.JSONDecodeError as e:
        raise Exception(f"Failed to parse JSON data: {e}")
    except Exception as e:
        raise Exception(f"Error processing country weights: {e}")
    
def calculate_portfolio_weights(portfolio, all_countries, region_weights_series, country_weights_df, market_cap_pct):
    """
    Calculate weights for each sector in the portfolio.
    
    Args:
        portfolio (dict): Portfolio definition
        all_countries (list): All available countries
        region_weights_series (pd.Series): Regional weights
        country_weights_df (pd.DataFrame): Country weights DataFrame
        market_cap_pct (dict): Market cap percentages
        
    Returns:
        pd.DataFrame: Portfolio weights DataFrame
    """
    portfolio_df = pd.DataFrame(columns=["Sector", "Market Caps", "Weight"])
    sector_weights = []
    
    for sector, caps in portfolio.items():
        cap_pct = sum([market_cap_pct[cap] for cap in caps])
        sector_weight = 0.0  # Initialize to prevent UnboundLocalError
        
        if sector == "All World":
            # Special case: use total world weight (should be 100%)
            sector_weight = 100.0 * (cap_pct / 100.0)
        elif sector in region_weights_series.index:
            sector_weight = region_weights_series[sector] * (cap_pct / 100.0)
        elif sector in all_countries:
            # Individual country
            country_weight = country_weights_df[country_weights_df['Country'] == sector]['Weight'].sum()
            sector_weight = country_weight * (cap_pct / 100.0)
        else:
            raise Exception(f"Warning: Sector '{sector}' not found in regions or countries.")
        
        sector_weights.append(sector_weight)
    
    portfolio_df['Sector'] = list(portfolio.keys())
    portfolio_df['Market Caps'] = list(portfolio.values())
    portfolio_df['Weight'] = sector_weights
    
    return portfolio_df

def analyze_world_coverage(portfolio, country_weights, region_groupings, all_countries, market_cap_pct):
    """
    Check portfolio coverage against world markets.
    
    Args:
        portfolio (dict): Portfolio definition
        country_weights (dict): Country weight mappings
        region_groupings (dict): Region to countries mapping
        all_countries (list): All available countries
        market_cap_pct (dict): Market cap percentages
        
    Returns:
        dict: Coverage analysis results
    """
    cap_coverage = {}
    pct_coverage = {}
    
    for sector, caps in portfolio.items():
        countries = get_countries_for_sector(sector, region_groupings, all_countries)
        
        if not countries:
            raise Exception(f"Unknown sector '{sector}' - skipping")
            
        for country in countries:
            if country not in country_weights:
                raise Exception(f"Country '{country}' not found in weights data")
                
            if country not in cap_coverage:
                cap_coverage[country] = sorted(caps)
                pct_coverage[country] = sum([
                    (country_weights[country]/100.0) * market_cap_pct[cap] 
                    for cap in caps
                ])
            else:
                cap_coverage[country] = sorted(cap_coverage[country] + caps)
                pct_coverage[country] += sum([
                    (country_weights[country]/100.0) * market_cap_pct[cap] 
                    for cap in caps
                ])
    
    # Check for overlaps and missing coverage
    overlapping_caps = {}
    missing_caps = {}
    overlapping_pct = {}
    missing_pct = {}
    
    all_caps = list(market_cap_pct.keys())
    for country, weight in country_weights.items():
        if country not in cap_coverage:
            cap_coverage[country] = []
            
        missing_caps_cur = [element for element in all_caps if element not in cap_coverage[country]]
        if missing_caps_cur:
            missing_caps[country] = missing_caps_cur
            missing_pct[country] = sum([
                (country_weights[country]/100.0) * market_cap_pct[cap] 
                for cap in missing_caps_cur
            ])
        
        extra_caps_cur = []
        for element in all_caps:
            if cap_coverage[country].count(element) > 1:
                extra_caps_cur.append(element)
        if extra_caps_cur:
            overlapping_caps[country] = extra_caps_cur
            overlapping_pct[country] = sum([
                (country_weights[country]/100.0) * market_cap_pct[cap] 
                for cap in extra_caps_cur
            ])
    
    return {
        'missing_caps': missing_caps,
        'missing_pct': missing_pct,
        'overlapping_caps': overlapping_caps,
        'overlapping_pct': overlapping_pct
    }

def print_coverage_report(results, portfolio_df):
    """Print coverage analysis report."""
    missing_caps = results['missing_caps']
    missing_pct = results['missing_pct']
    overlapping_caps = results['overlapping_caps']
    overlapping_pct = results['overlapping_pct']
    
    if not missing_caps and not overlapping_caps:
        print(f"Total market coverage={portfolio_df['Weight'].sum():.2f}%. No overlaps or missing segments.")
    
    if missing_caps:
        print(f"Missing segments: {missing_caps}")
        print(f"Missing coverage: {missing_pct}")
        print(f"Total market coverage={portfolio_df['Weight'].sum():.2f}%, "
              f"Total missed coverage: {sum(missing_pct.values()):.2f}%")
    
    if overlapping_caps:
        print(f"Overlapping segments: {overlapping_caps}")
        print(f"Overlapping coverage: {overlapping_pct}")
        print(f"Total market coverage={portfolio_df['Weight'].sum():.2f}%, "
              f"Total overlapping coverage: {sum(overlapping_pct.values()):.2f}%")

def main(file_path):
    """
    Main execution function.
    
    Args:
        file_path (str): Path to portfolio YAML file
    """
    # load configurations
    region_groupings, all_countries = load_regions()
    config = read_yaml("config.yaml")
    market_cap_pct = config['market_caps']
    imid_url = config['data_sources']['url']

    # load portfolio definition:
    portfolio = read_yaml(file_path)

    # validate portfolio sectors
    valid_sectors, invalid_sectors = validate_portfolio_sectors(portfolio, region_groupings, all_countries)
    if invalid_sectors:
        raise Exception(f"Unknown sectors in portfolio: {invalid_sectors}. Make sure they appear in the regions.yaml file as a region or country.")
    
    # fetch country weights from IMID
    country_weights_df = fetch_country_weights(imid_url)

    # add missing countries with 0 weight
    missing_countries = set(all_countries) - set(country_weights_df['Country'])
    if missing_countries:
        print(f"Adding {len(missing_countries)} missing countries with 0% weight: {missing_countries}")
        for country in missing_countries:
            country_weights_df.loc[len(country_weights_df)] = {'Country': country, 'Weight': 0.00}

    # build region weights by grouping countries
    region_weights = {}
    for region_name, countries in region_groupings.items():
        region_weight = country_weights_df[country_weights_df['Country'].isin(countries)]['Weight'].sum()
        region_weights[region_name] = region_weight
    
    region_weights_series = pd.Series(region_weights).sort_values(ascending=False)
        
    print("Region Weights:")
    print(region_weights_series)    
    
    # calculate portfolio weights
    portfolio_df = calculate_portfolio_weights(
        portfolio, all_countries, 
        region_weights_series, country_weights_df, market_cap_pct
    )
    
    print(f"\nPortfolio Weights:")
    print(portfolio_df)

    # analyze coverage
    country_weights = country_weights_df.set_index('Country')['Weight'].to_dict()
    results = analyze_world_coverage(
        portfolio, country_weights, region_groupings, 
        all_countries, market_cap_pct
    )
    
    print("\n" + "="*50)
    print_coverage_report(results, portfolio_df)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Calculate portfolio weights for global equity diversification",
        epilog="Example: python calculate_portfolio_weights.py --file portfolios/perfect_with_SNP500.yaml"
    )
    parser.add_argument(
        '--file', 
        type=str, 
        help="Path to the YAML portfolio definition file", 
        default="portfolios/perfect_with_SNP500.yaml"
    )
    args = parser.parse_args()
    main(args.file)

