"""Shared fixtures for the dashboard test suite (repo root on sys.path first)."""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from dashboard.services import data_loader as load  # noqa: E402


@pytest.fixture(scope="session")
def queue() -> pd.DataFrame:
    return load.load_review_queue()


@pytest.fixture(scope="session")
def evidence() -> pd.DataFrame:
    return load.load_evidence()


@pytest.fixture(scope="session")
def panel() -> pd.DataFrame:
    return load.load_panel()


@pytest.fixture(scope="session")
def features() -> pd.DataFrame:
    return load.load_features()


@pytest.fixture(scope="session")
def comparison() -> pd.DataFrame:
    return load.load_model_comparison()


@pytest.fixture(scope="session")
def content() -> dict:
    return load.load_content()
