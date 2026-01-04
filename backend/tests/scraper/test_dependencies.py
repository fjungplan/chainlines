"""Test that scraper dependencies are installed correctly."""
import pytest

def test_instructor_installed():
    import instructor
    assert instructor is not None

def test_google_generativeai_installed():
    import google.generativeai
    assert google.generativeai is not None

def test_openai_installed():
    import openai
    assert openai is not None
