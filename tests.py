#!/usr/bin/env python3
"""
Test suite for portfolio diversity calculator.
Run with: python tests.py
Or specific test: python tests.py TestCoverage.test_perfect_portfolio
"""

import sys
import unittest

from utils import get_countries_for_sector, load_regions, read_yaml


class TestCoverage(unittest.TestCase):
    """Test portfolio coverage validation."""

    @classmethod
    def setUpClass(cls):
        """Load configuration once for all tests."""
        cls.region_groupings, cls.all_countries = load_regions()
        cls.config = read_yaml("config.yaml")
        cls.market_cap_pct = cls.config["market_caps"]

    def check_world_coverage(self, portfolio):
        """
        Check that portfolio components fully and without overlaps cover
        all market caps for each country in MSCI ACWI IMI.

        Returns:
            tuple: (is_perfect, coverage_details)
        """
        cap_coverage = {}

        for sector, caps in portfolio.items():
            countries = get_countries_for_sector(sector, self.region_groupings, self.all_countries)

            for country in countries:
                if country not in cap_coverage:
                    cap_coverage[country] = sorted(caps)
                else:
                    cap_coverage[country] = sorted(cap_coverage[country] + caps)

        if not cap_coverage:
            return False, "No coverage found"

        # Expected full coverage: all market cap types
        expected_coverage = sorted(list(self.market_cap_pct.keys()))

        # Check if all countries have identical AND complete coverage
        cap_coverage_values = list(cap_coverage.values())
        first_value = cap_coverage_values[0]
        all_same = all(val == first_value for val in cap_coverage_values)

        if all_same and first_value == expected_coverage:
            return True, f"Perfect coverage: all {len(cap_coverage)} countries have {first_value}"
        elif all_same and first_value != expected_coverage:
            missing = set(expected_coverage) - set(first_value)
            extra = set(first_value) - set(expected_coverage)
            details = []
            if missing:
                details.append(f"missing {sorted(missing)}")
            if extra:
                details.append(f"extra {sorted(extra)}")
            return (
                False,
                f"Incomplete coverage: all countries have {first_value}, but {', '.join(details)}",
            )
        else:
            inconsistent = {
                country: coverage
                for country, coverage in cap_coverage.items()
                if coverage != first_value
            }
            return False, f"Inconsistent coverage: {inconsistent}"

    def test_perfect_portfolio(self):
        """Test that perfect_with_SNP500 portfolio has complete coverage."""
        portfolio = read_yaml("portfolios/perfect_with_SNP500.yaml")
        is_perfect, details = self.check_world_coverage(portfolio)
        self.assertTrue(is_perfect, f"Perfect portfolio failed: {details}")

    def test_imid_portfolio(self):
        """Test that IMID portfolio (All World) has complete coverage."""
        portfolio = read_yaml("portfolios/IMID.yaml")
        is_perfect, details = self.check_world_coverage(portfolio)
        self.assertTrue(is_perfect, f"IMID portfolio failed: {details}")

    def test_approximate_portfolio_incomplete(self):
        """Test that approximate portfolio is recognized as incomplete."""
        portfolio = read_yaml("portfolios/approximate_with_SNP500.yaml")
        is_perfect, details = self.check_world_coverage(portfolio)
        self.assertFalse(is_perfect, "Approximate portfolio should not have perfect coverage")

    def test_ssac_portfolio_incomplete(self):
        """Test that SSAC portfolio (Large+Medium only) is incomplete."""
        portfolio = read_yaml("portfolios/SSAC.yaml")
        is_perfect, details = self.check_world_coverage(portfolio)
        self.assertFalse(
            is_perfect, "SSAC portfolio should not have perfect coverage (missing Small caps)"
        )


class TestRegions(unittest.TestCase):
    """Test region and country mappings."""

    @classmethod
    def setUpClass(cls):
        """Load configuration once for all tests."""
        cls.region_groupings, cls.all_countries = load_regions()

    def test_developed_and_emerging_cover_all(self):
        """Test that Developed + Emerging regions cover all countries."""
        developed = set(self.region_groupings.get("Developed", []))
        emerging = set(self.region_groupings.get("Emerging", []))
        all_from_markets = developed | emerging

        self.assertEqual(
            set(self.all_countries),
            all_from_markets,
            "Developed + Emerging should cover all countries",
        )

    def test_developed_europe_subset_of_developed(self):
        """Test that Developed Europe countries are all in Developed market."""
        developed = set(self.region_groupings.get("Developed", []))
        developed_europe = set(self.region_groupings.get("Developed Europe", []))

        self.assertTrue(
            developed_europe.issubset(developed), "Developed Europe should be subset of Developed"
        )

    def test_pacific_ex_japan_subset_of_developed(self):
        """Test that Pacific ex Japan countries are all in Developed market."""
        developed = set(self.region_groupings.get("Developed", []))
        pacific_ex_japan = set(self.region_groupings.get("Developed Pacific ex Japan", []))

        self.assertTrue(
            pacific_ex_japan.issubset(developed), "Pacific ex Japan should be subset of Developed"
        )


class TestUtilities(unittest.TestCase):
    """Test utility functions."""

    @classmethod
    def setUpClass(cls):
        """Load configuration once for all tests."""
        cls.region_groupings, cls.all_countries = load_regions()
        cls.config = read_yaml("config.yaml")

    def test_load_config(self):
        """Test that configuration loads correctly."""
        self.assertIn("market_caps", self.config)
        self.assertIn("data_sources", self.config)
        self.assertEqual(self.config["market_caps"]["Large"], 70)

    def test_get_countries_for_all_world(self):
        """Test that 'All World' returns all countries."""
        countries = get_countries_for_sector("All World", self.region_groupings, self.all_countries)
        self.assertEqual(set(countries), set(self.all_countries))

    def test_get_countries_for_region(self):
        """Test that region lookup works correctly."""
        countries = get_countries_for_sector(
            "Developed Europe", self.region_groupings, self.all_countries
        )
        expected = self.region_groupings["Developed Europe"]
        self.assertEqual(set(countries), set(expected))

    def test_get_countries_for_individual_country(self):
        """Test that individual country lookup works."""
        countries = get_countries_for_sector(
            "United States", self.region_groupings, self.all_countries
        )
        self.assertEqual(countries, ["United States"])

    def test_get_countries_for_invalid_sector(self):
        """Test that invalid sector returns empty list."""
        countries = get_countries_for_sector(
            "Invalid Sector", self.region_groupings, self.all_countries
        )
        self.assertEqual(countries, [])


class TestMarketCapAssumptions(unittest.TestCase):
    """Test market cap distribution assumptions."""

    @classmethod
    def setUpClass(cls):
        """Load configuration once for all tests."""
        cls.config = read_yaml("config.yaml")
        cls.market_cap_pct = cls.config["market_caps"]

    def test_market_caps_sum_to_100(self):
        """Test that market cap percentages sum to 100."""
        total = sum(self.market_cap_pct.values())
        self.assertEqual(total, 100, "Market cap percentages should sum to 100%")

    def test_all_caps_present(self):
        """Test that all expected market caps are defined."""
        expected_caps = {"Large", "Medium", "Small"}
        actual_caps = set(self.market_cap_pct.keys())
        self.assertEqual(actual_caps, expected_caps, "Should have Large, Medium, and Small caps")


def run_tests_with_verbose_output():
    """Run tests with detailed output."""
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestCoverage))
    suite.addTests(loader.loadTestsFromTestCase(TestRegions))
    suite.addTests(loader.loadTestsFromTestCase(TestUtilities))
    suite.addTests(loader.loadTestsFromTestCase(TestMarketCapAssumptions))

    # Run with verbose output
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Return exit code based on success
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    # If specific test is provided as argument, use unittest's default behavior
    if len(sys.argv) > 1 and not sys.argv[1].startswith("-"):
        unittest.main()
    else:
        # Otherwise, run our custom verbose test runner
        sys.exit(run_tests_with_verbose_output())
