# utils.py
"""
Utility functions for portfolio diversity calculation.
Handles file I/O, configuration loading, and portfolio validation.
"""

import yaml

def read_yaml(file_path):
    """Read YAML file."""
    with open(file_path, 'r') as file:
        return yaml.safe_load(file)


def load_regions(regions_file="regions.yaml"):
    """
    Load region groupings from YAML file.
    
    Returns:
        tuple: (region_groupings, all_countries)
    """
    region_groupings = read_yaml(regions_file)
    
    # Get all unique countries
    all_countries = set()
    for countries in region_groupings.values():
        all_countries.update(countries)
    all_countries = sorted(list(all_countries))
    
    return region_groupings, all_countries


def load_config(config_file="config.yaml"):
    """
    Load configuration from YAML file.
    
    Returns:
        dict: Configuration dictionary
    """
    return read_yaml(config_file)


def validate_portfolio_sectors(portfolio, region_groupings, all_countries):
    """
    Validate that all portfolio sectors exist in the data.
    
    Returns:
        tuple: (valid_sectors, invalid_sectors)
    """
    valid_sectors = []
    invalid_sectors = []
    
    for sector in portfolio.keys():
        if (sector in region_groupings or 
            sector in all_countries or 
            sector == "All World"):
            valid_sectors.append(sector)
        else:
            invalid_sectors.append(sector)
    
    return valid_sectors, invalid_sectors


def get_countries_for_sector(sector, region_groupings, all_countries):
    """
    Get list of countries for a given sector.
    
    Args:
        sector (str): Sector name
        region_groupings (dict): Region to countries mapping
        all_countries (list): All available countries
        
    Returns:
        list: Countries in this sector
    """
    if sector == "All World":
        return all_countries
    elif sector in region_groupings:
        return region_groupings[sector]
    elif sector in all_countries:
        return [sector]
    else:
        return []