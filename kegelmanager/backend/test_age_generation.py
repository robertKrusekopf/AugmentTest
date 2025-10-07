"""
Test script for age generation based on altersklasse.
"""

import sys
sys.path.insert(0, '.')

from init_db import get_age_range_for_altersklasse

def test_age_ranges():
    """Test the age range function with different altersklasse values."""
    
    test_cases = [
        ("Herren", (18, 35)),
        ("A-Jugend", (17, 18)),
        ("A Jugend", (17, 18)),
        ("a-jugend", (17, 18)),  # Test case-insensitivity
        ("A", (17, 18)),  # Test short form
        ("a", (17, 18)),  # Test short form lowercase
        ("B-Jugend", (15, 16)),
        ("B", (15, 16)),  # Test short form
        ("C-Jugend", (13, 14)),
        ("C", (13, 14)),  # Test short form
        ("D-Jugend", (11, 12)),
        ("D", (11, 12)),  # Test short form
        ("E-Jugend", (9, 10)),
        ("E", (9, 10)),  # Test short form
        ("F-Jugend", (7, 8)),
        ("F", (7, 8)),  # Test short form
        (None, (18, 35)),  # Test None
        ("", (18, 35)),  # Test empty string
        ("Unbekannt", (18, 35)),  # Test unknown value
    ]
    
    print("Testing get_age_range_for_altersklasse():")
    print("-" * 50)
    
    all_passed = True
    for altersklasse, expected in test_cases:
        result = get_age_range_for_altersklasse(altersklasse)
        passed = result == expected
        all_passed = all_passed and passed
        
        status = "✓" if passed else "✗"
        print(f"{status} {str(altersklasse):20s} -> {result} (expected: {expected})")
    
    print("-" * 50)
    if all_passed:
        print("All tests passed! ✓")
    else:
        print("Some tests failed! ✗")
    
    return all_passed

if __name__ == "__main__":
    success = test_age_ranges()
    sys.exit(0 if success else 1)

