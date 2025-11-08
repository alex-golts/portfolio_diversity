#!/usr/bin/env python3
"""
Visualization module for portfolio diversity analysis.
Creates charts comparing portfolio coverage against world market composition.

Usage:
    python visualize.py --file portfolios/perfect_with_SNP500.yaml
    python visualize.py --file portfolios/approximate_with_SNP500.yaml --output charts/
"""

import argparse
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from calculate_portfolio_weights import fetch_country_weights
from utils import get_countries_for_sector, load_regions, read_yaml


def plot_coverage_heatmap(
    portfolio, country_weights_df, region_groupings, all_countries, market_cap_pct, output_path=None
):
    """
    Create heatmap showing coverage status for each country and market cap segment.

    Args:
        portfolio: Portfolio definition dict
        country_weights_df: DataFrame with country weights
        region_groupings: Region to countries mapping
        all_countries: List of all countries
        market_cap_pct: Market cap percentages dict
        output_path: Optional path to save the figure
    """
    # Build coverage matrix
    cap_coverage = {}

    for sector, caps in portfolio.items():
        countries = get_countries_for_sector(sector, region_groupings, all_countries)

        for country in countries:
            if country not in cap_coverage:
                cap_coverage[country] = {cap: 0 for cap in market_cap_pct.keys()}
            for cap in caps:
                cap_coverage[country][cap] += 1

    # Select top countries by weight for visualization (otherwise too many)
    top_countries = country_weights_df.nlargest(30, "Weight")["Country"].tolist()

    # Build matrix for heatmap
    cap_types = sorted(market_cap_pct.keys(), key=lambda x: market_cap_pct[x], reverse=True)
    matrix_data = []
    countries_in_matrix = []

    for country in top_countries:
        if country in cap_coverage:
            row = [cap_coverage[country].get(cap, 0) for cap in cap_types]
            matrix_data.append(row)
            countries_in_matrix.append(country)

    if not matrix_data:
        print("⚠️  No coverage data to visualize")
        return None

    # Create heatmap
    fig, ax = plt.subplots(figsize=(8, 12))

    # Color mapping: 0=red (missing), 1=green (covered), 2+=yellow (overlap)
    matrix = np.array(matrix_data)

    # Create custom colormap
    cmap = plt.cm.colors.ListedColormap(["#e74c3c", "#2ecc71", "#f39c12"])
    bounds = [-0.5, 0.5, 1.5, 2.5]
    norm = plt.cm.colors.BoundaryNorm(bounds, cmap.N)

    im = ax.imshow(matrix, cmap=cmap, norm=norm, aspect="auto")

    # Set ticks and labels
    ax.set_xticks(np.arange(len(cap_types)))
    ax.set_yticks(np.arange(len(countries_in_matrix)))
    ax.set_xticklabels(cap_types)
    ax.set_yticklabels(countries_in_matrix)

    # Rotate the tick labels for better readability
    plt.setp(ax.get_xticklabels(), rotation=0, ha="center")

    # Add title and labels
    ax.set_title(
        "Portfolio Coverage by Country and Market Cap\n(Top 30 Countries by Weight)",
        fontsize=12,
        fontweight="bold",
        pad=15,
    )
    ax.set_xlabel("Market Cap Segment", fontsize=11, fontweight="bold")
    ax.set_ylabel("Country", fontsize=11, fontweight="bold")

    # Add text annotations
    for i in range(len(countries_in_matrix)):
        for j in range(len(cap_types)):
            value = matrix[i, j]
            if value == 0:
                text = "✗"
                color = "white"
            elif value == 1:
                text = "✓"
                color = "white"
            else:
                text = f"{int(value)}x"
                color = "black"
            ax.text(
                j, i, text, ha="center", va="center", color=color, fontsize=10, fontweight="bold"
            )

    # Add colorbar legend
    cbar = plt.colorbar(im, ax=ax, ticks=[0, 1, 2])
    cbar.ax.set_yticklabels(["Missing", "Covered", "Overlap"])

    plt.tight_layout()

    if output_path:
        plt.savefig(output_path, dpi=300, bbox_inches="tight")
        print(f"✅ Saved coverage heatmap to {output_path}")
    else:
        plt.show()

    return fig


def plot_country_level_comparison(
    portfolio,
    country_weights_df,
    region_groupings,
    all_countries,
    market_cap_pct,
    output_path=None,
    top_n=25,
    sort_ascending=True,
):
    """
    Create detailed country-level comparison showing ideal vs actual allocation.
    Shows grouped bars with ideal and actual using same colors but separated by white gap.

    Args:
        portfolio: Portfolio definition dict
        country_weights_df: DataFrame with country weights
        region_groupings: Region to countries mapping
        all_countries: List of all countries
        market_cap_pct: Market cap percentages dict
        output_path: Optional path to save the figure
        top_n: Number of top countries to display (default 25)
        sort_ascending: If True (default), largest countries at top; if False, smallest at top
    """
    # Calculate ideal allocation per country per cap
    ideal_allocation = {}
    for country in all_countries:
        country_weight = country_weights_df[country_weights_df["Country"] == country]["Weight"]
        if not country_weight.empty:
            total_weight = country_weight.values[0]
            ideal_allocation[country] = {
                cap: total_weight * (market_cap_pct[cap] / 100.0) for cap in market_cap_pct.keys()
            }

    # Calculate actual portfolio allocation per country per cap
    actual_allocation = {}
    for sector, caps in portfolio.items():
        countries = get_countries_for_sector(sector, region_groupings, all_countries)

        for country in countries:
            if country not in actual_allocation:
                actual_allocation[country] = {cap: 0.0 for cap in market_cap_pct.keys()}

            country_weight = country_weights_df[country_weights_df["Country"] == country]["Weight"]
            if not country_weight.empty:
                total_weight = country_weight.values[0]
                for cap in caps:
                    actual_allocation[country][cap] += total_weight * (market_cap_pct[cap] / 100.0)

    # Select top N countries by total weight
    top_countries_df = country_weights_df.nlargest(top_n, "Weight")

    # Sort according to parameter - note that y-axis is reversed (0 at top)
    # So ascending=True means largest countries have smallest y-values (appear at top)
    if sort_ascending:
        # Largest at top (ascending weight values = descending visual order)
        top_countries_df = top_countries_df.sort_values("Weight", ascending=True)
    else:
        # Smallest at top (descending weight values = ascending visual order)
        top_countries_df = top_countries_df.sort_values("Weight", ascending=False)

    top_countries = top_countries_df["Country"].tolist()

    # Prepare data for plotting
    cap_types = sorted(market_cap_pct.keys(), key=lambda x: market_cap_pct[x], reverse=True)

    # Build data arrays
    countries_list = []
    ideal_totals = []
    actual_totals = []
    ideal_data = {cap: [] for cap in cap_types}
    actual_data = {cap: [] for cap in cap_types}

    for country in top_countries:
        if country in ideal_allocation:
            countries_list.append(country)

            # Calculate totals
            ideal_total = sum(ideal_allocation[country].values())
            actual_total = sum(actual_allocation.get(country, {}).values())
            ideal_totals.append(ideal_total)
            actual_totals.append(actual_total)

            for cap in cap_types:
                ideal_data[cap].append(ideal_allocation[country].get(cap, 0))
                actual_data[cap].append(actual_allocation.get(country, {}).get(cap, 0))

    if not countries_list:
        print("⚠️  No country data to visualize")
        return None

    # Create single plot with two bars per country separated by white line
    fig, ax = plt.subplots(figsize=(14, 12))

    # Colors for each cap type
    colors = {"Large": "#3498db", "Medium": "#9b59b6", "Small": "#e74c3c"}

    y_pos = np.arange(len(countries_list))
    bar_height = 0.35
    gap = 0.02  # Small white gap between the two bars

    # Plot ideal allocation (top bar)
    bottom_ideal = np.zeros(len(countries_list))
    for cap in cap_types:
        values = np.array(ideal_data[cap])
        ax.barh(
            y_pos - bar_height / 2 - gap / 2,
            values,
            bar_height,
            left=bottom_ideal,
            color=colors.get(cap, "#95a5a6"),
            edgecolor="white",
            linewidth=1.5,
        )
        bottom_ideal += values

    # Plot actual allocation (bottom bar) - same colors
    bottom_actual = np.zeros(len(countries_list))
    for cap in cap_types:
        values = np.array(actual_data[cap])
        ax.barh(
            y_pos + bar_height / 2 + gap / 2,
            values,
            bar_height,
            left=bottom_actual,
            color=colors.get(cap, "#95a5a6"),
            edgecolor="white",
            linewidth=1.5,
        )
        bottom_actual += values

    # Use standard log scale
    ax.set_xscale("log")
    ax.set_xlim(left=0.1)

    # Add grid at specific intervals
    ax.grid(axis="x", alpha=0.3, linestyle="--", which="both")

    # Add legend elements - positioned at lower right (where small countries are)
    from matplotlib.patches import Patch

    legend_elements = [
        Patch(
            facecolor="lightgray",
            edgecolor="black",
            linewidth=1,
            label="Top bar = Your Portfolio (Actual)",
        ),
        Patch(
            facecolor="lightgray",
            edgecolor="black",
            linewidth=1,
            label="Bottom bar = World Market (Ideal)",
        ),
        Patch(facecolor="white", label=""),  # Spacer
    ]

    # Add cap type colors to legend
    for cap in cap_types:
        legend_elements.append(Patch(facecolor=colors.get(cap, "#95a5a6"), label=f"{cap} Cap"))

    ax.legend(handles=legend_elements, loc="lower right", fontsize=9)

    ax.set_yticks(y_pos)
    ax.set_yticklabels(countries_list)
    ax.set_xlabel("Weight (% of Global Market, log scale)", fontsize=12, fontweight="bold")

    sort_desc = "largest→smallest" if sort_ascending else "smallest→largest"
    ax.set_title(
        "Country-Level Allocation: World Market vs Your Portfolio\n"
        + f"(Top {len(countries_list)} Countries, {sort_desc})",
        fontsize=13,
        fontweight="bold",
        pad=20,
    )
    ax.grid(axis="x", alpha=0.3, linestyle="--", which="both")

    # Add text annotations showing coverage percentage
    for i, (country, ideal, actual) in enumerate(zip(countries_list, ideal_totals, actual_totals)):
        if ideal > 0:
            coverage_pct = (actual / ideal) * 100
            if coverage_pct < 50:
                color = "#e74c3c"  # Red for low coverage
                symbol = "⚠️"
                text = f"{symbol} {coverage_pct:.0f}%"
            elif coverage_pct < 100:
                color = "#f39c12"  # Orange for partial
                symbol = "◐"
                text = f"{symbol} {coverage_pct:.0f}%"
            else:  # coverage_pct >= 100
                color = "#2ecc71"  # Green for complete
                symbol = "●"
                text = f"{symbol} 100%"

            # Place annotation to the right of the bars
            max_val = max(ideal, actual)
            ax.text(max_val * 1.5, i, text, va="center", fontsize=8, color=color, fontweight="bold")

    plt.tight_layout()

    if output_path:
        plt.savefig(output_path, dpi=300, bbox_inches="tight")
        print(f"✅ Saved country-level comparison to {output_path}")
    else:
        plt.show()

    return fig


def plot_all_visualizations(portfolio_file, output_dir=None):
    """
    Generate all visualizations for a portfolio.

    Args:
        portfolio_file: Path to portfolio YAML file
        output_dir: Optional directory to save figures
    """
    print(f"📊 Generating visualizations for {portfolio_file}...")

    # Load configuration
    region_groupings, all_countries = load_regions()
    config = read_yaml("config.yaml")
    market_cap_pct = config["market_caps"]
    imid_url = config["data_sources"]["url"]

    # Load portfolio
    portfolio = read_yaml(portfolio_file)

    # Fetch country weights
    df = fetch_country_weights(imid_url)

    # Add missing countries
    missing_countries = set(all_countries) - set(df["Country"])
    for country in missing_countries:
        df.loc[len(df)] = {"Country": country, "Weight": 0.00}

    # Build region weights
    region_weights = {}
    for region_name, countries in region_groupings.items():
        region_weight = df[df["Country"].isin(countries)]["Weight"].sum()
        region_weights[region_name] = region_weight

    # Create output directory if specified
    if output_dir:
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        portfolio_name = Path(portfolio_file).stem

        # Generate all plots (pass df for country weights)
        plot_coverage_heatmap(
            portfolio,
            df,
            region_groupings,
            all_countries,
            market_cap_pct,
            f"{output_dir}/{portfolio_name}_heatmap.png",
        )
        plot_country_level_comparison(
            portfolio,
            df,
            region_groupings,
            all_countries,
            market_cap_pct,
            f"{output_dir}/{portfolio_name}_country_detail.png",
        )
    else:
        # Show plots interactively (pass df for country weights)
        plot_coverage_heatmap(portfolio, df, region_groupings, all_countries, market_cap_pct)
        plot_country_level_comparison(
            portfolio, df, region_groupings, all_countries, market_cap_pct
        )

    print("✅ Visualization complete!")


def main():
    """Main entry point for visualization script."""
    parser = argparse.ArgumentParser(
        description="Visualize portfolio coverage and composition",
        epilog="Example: python visualize.py --file portfolios/perfect_with_SNP500.yaml --output charts/",
    )
    parser.add_argument("--file", type=str, required=True, help="Path to the portfolio YAML file")
    parser.add_argument(
        "--output",
        type=str,
        help="Output directory for saving charts (if not specified, displays interactively)",
    )

    args = parser.parse_args()

    try:
        plot_all_visualizations(args.file, args.output)
    except FileNotFoundError as e:
        print(f"❌ Error: File not found - {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
