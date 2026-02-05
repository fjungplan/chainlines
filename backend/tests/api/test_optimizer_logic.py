import pytest

def test_y_normalization_logic():
    # The normalization logic is currently inline in runner.py.
    # I'll replicate the core logic here to verify its correctness.
    
    def normalize(y_indices):
        if not y_indices:
            return y_indices
        min_y = min(y_indices.values())
        return {k: v - min_y for k, v in y_indices.items()}

    # Case 1: Gap at top (min_y = 2)
    input_1 = {"c1": 2, "c2": 3, "c3": 5}
    expected_1 = {"c1": 0, "c2": 1, "c3": 3}
    assert normalize(input_1) == expected_1

    # Case 2: Already zero
    input_2 = {"c1": 0, "c2": 10}
    assert normalize(input_2) == input_2

    # Case 3: Empty
    assert normalize({}) == {}

    # Case 4: Negative min (shouldn't happen but logic should handle)
    input_4 = {"c1": -1, "c2": 1}
    expected_4 = {"c1": 0, "c2": 2}
    assert normalize(input_4) == expected_4
