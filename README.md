# Portfolio Diversity Calculator

A tool for calculating optimal portfolio weights to track global equity markets when direct investment in a world index ETF isn't feasible or optimal.

## Problem Statement

Sometimes you can't simply buy a single world index ETF due to various constraints:

- **Limited Options**: Your pension fund only offers S&P 500, but you want global diversification across all your accounts
- **Cost Optimization**: Combining multiple ETFs for lower overall expense ratios
- **Flexibility**: Want control over regional allocations while maintaining world market exposure (for example, if specific region ETFs are traded in your local stock exchange and you can buy them at low comission and/or favorable taxation policy)

## Solution

This tool calculates how much to weight different geographic sectors/ETFs so that your **combined portfolio** tracks the MSCI All Country World Index Investable Market Index (ACWI IMI) - the most comprehensive global equity benchmark, as closely as possible.

## How It Works

1. **Fetches Real Data**: Scrapes current country weights from the SPDR MSCI ACWI IMI ETF (IMID), which is assumed to track the benchmark index near perfectly.
2. **Calculates Weights**: Determines optimal allocation for each sector in your portfolio definition
3. **Validates Coverage**: Checks for gaps, overlaps, or perfect world market coverage
4. **Provides Analysis**: Shows exactly what percentage of global markets you're capturing

## Quick Start

```bash
# Calculate weights for a recommended (for non-US investors) "perfect coverage" portfolio
python calculate_portfolio_weights.py --file portfolios/perfect_with_SNP500.yaml

# Test coverage validation
python test_coverage.py portfolios/perfect_with_SNP500.yaml

# Try a simpler approximate portfolio
python calculate_portfolio_weights.py --file portfolios/approximate_with_SNP500.yaml
```

## Portfolio Types

### 🎯 Perfect Coverage (Recommended for non US investors)

**File**: `portfolios/perfect_with_SNP500.yaml`

```yaml
United States:
  - Medium
  - Large
Developed Europe:
  - Medium
  - Large
Emerging:
  - Small
  - Medium
  - Large
Developed:
  - Small
Japan:
  - Medium
  - Large
Developed Pacific ex Japan:
  - Medium
  - Large
Canada:
  - Medium
  - Large
Israel:
  - Medium
  - Large
```

* Note: for US investors, a combination of US + Global ex US (like VTI+VXUS) may be preferrable.

**✅ Advantages**:
- **100% Global Coverage**: Captures the entire MSCI ACWI IMI index with solid UCITS ETFs tracking MSCI based indexes.
- **Zero Overlaps**: Each country/market cap combination appears exactly once
- **Optimal Diversification**: True global equity exposure

**💰 Real-World Use Case**: 
- Pension fund: S&P 500 only → covers "United States" Large+Medium caps
- Personal account: Weight the remaining sectors to achieve global balance

### 📊 Approximate Coverage

**File**: `portfolios/approximate_with_SNP500.yaml`

```yaml
United States:
  - Medium
  - Large
Developed Europe:
  - Medium
  - Large
Emerging:
  - Small
  - Medium
  - Large
```

**⚖️ Trade-offs**:
- **Simpler**: Only 3 sectors/ETFs needed
- **Good Coverage**: ~85-90% of global markets
- **Missing**: Japan, Canada, Pacific ex-Japan, Small-cap developed markets
- **Use Case**: When you want "good enough" global exposure with minimal complexity

### 🎯 Single ETF Equivalent

**File**: `portfolios/IMID.yaml`

```yaml
All World:
  - Small
  - Medium
  - Large
```

**Purpose**: Mainly here as a sanity test. It's clear that buying IMID directly gives you 100% coverage (baseline comparison)

## Real-World Examples

### Example 1: US Pension Fund + Personal Account
**Problem**: Your 401k only offers Vanguard S&P 500, but you want global exposure across all accounts.

**Solution**:
1. Keep 401k in S&P 500 (covers "United States" Large+Medium)
2. In personal account, buy ETFs covering remaining sectors with calculated weights:
   - Developed Europe ETF: 13.8% of total portfolio
   - Emerging Markets ETF: 11.8% of total portfolio
   - Japan ETF: 5.0% of total portfolio
   - etc.
   Alternatively, add "ex US" sector to `regions.yaml` since there are such US funds, and supplement your S&P 500 investment with that.

**Result**: Combined portfolio tracks global equity markets perfectly.

### Example 2: Cost Optimization
**Problem**: IMID ETF has 0.17% expense ratio, but can you do better?

**Solution**:
1. Use tool to determine weights for low-cost regional ETFs
2. Combine multiple ETFs to achieve a lower weighted expense ratio.

## File Structure

```
├── calculate_portfolio_weights.py  # Main calculator
├── test_coverage.py               # Coverage validation tool
├── utils.py                       # Utility functions
├── regions.yaml                   # Geographic groupings
├── config.yaml                    # Application settings
└── portfolios/                    # Portfolio definitions
    ├── perfect_with_SNP500.yaml   # 🎯 Recommended: Perfect coverage
    ├── approximate_with_SNP500.yaml # Simple approximation
    ├── IMID.yaml                  # Single ETF baseline
    └── SSAC.yaml                  # Large+Medium caps only
```

## Understanding the Output

### Weight Calculation
```
Portfolio Weights:
Sector                           Market Caps              Weight
United States                    [Medium, Large]          52.28
Developed Europe                 [Medium, Large]          13.77
Emerging                         [Small, Medium, Large]   11.80
...
```

### Coverage Analysis
```
✅ Total market coverage=100.00%. No overlaps or missing segments.
```

Or for incomplete portfolios:
```
⚠️ Missing segments: {'Japan': ['Small'], 'Canada': ['Small']}
📊 Total market coverage=94.50%, Total missed coverage: 5.50%
```

## Configuration

### Adding New Regions


Edit `regions.yaml`:
```yaml
# Add custom regional groupings
Nordic Countries:
  - Denmark
  - Finland
  - Norway
  - Sweden

World ex US:
  - ...
  - ...

```

### Defining a new portfolio
Create a new portfolio `.yaml` file listing regions or individual countries and cap size breakdown, according to the ETFs you wish to buy, for example:

```yaml
United States:
  - Small
  - Medium
  - Large
World ex US:
  - Small
  - Medium
  - Large
```


### Adjusting Market Cap Distribution

Edit `config.yaml`:
```yaml
market_caps:
  Large: 70    # Adjust these percentages based on your
  Medium: 15   # preferred market cap methodology
  Small: 15
```

## Installation

### Requirements
```bash
pip install requests beautifulsoup4 pandas pyyaml
```

### Setup
```bash
git clone <repository-url>
cd portfolio-diversity
python calculate_portfolio_weights.py --help
```

## Methodology

### Market Cap Assumptions
- **Large Cap**: 70% of country's market
- **Medium Cap**: 15% of country's market  
- **Small Cap**: 15% of country's market

*These percentages approximate MSCI's methodology and can be adjusted in `config.yaml`*

### Geographic Classifications
Based on MSCI country classifications:
- **Developed Markets**: US, Europe, Japan, etc.
- **Emerging Markets**: China, India, Brazil, etc.
- **Regional Subdivisions**: Developed Europe, Pacific ex-Japan, etc.

## License

MIT License - see LICENSE file for details.

## Disclaimer

This tool is for educational and planning purposes. Always verify calculations and consult with financial advisors before making investment decisions. Market data accuracy depends on the reliability of source websites.