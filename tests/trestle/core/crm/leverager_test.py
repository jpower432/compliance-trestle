# -*- mode:python; coding:utf-8 -*-
# Copyright (c) 2020 IBM Corp. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Tests for Leverager."""

import logging
from typing import List

import pytest

import trestle.core.generators as gens
import trestle.oscal.ssp as ossp
from trestle.core.crm.leverager import Leverager

logger = logging.getLogger(__name__)


@pytest.fixture
def sample_leveraging_ssp() -> ossp.SystemSecurityPlan:
    """Return a generated leveraging SSP."""
    return gens.generate_sample_model(ossp.SystemSecurityPlan)


@pytest.fixture
def sample_leveraged_components() -> List[ossp.SystemComponent]:
    """Return a list of generated leveraged components."""
    return [gens.generate_sample_model(ossp.SystemComponent) for _ in range(3)]


@pytest.fixture
def sample_ssp_path() -> str:
    """Return a sample ssp path."""
    return str('path/to/leveraged/ssp')


def test_create_leveraged_authz(sample_leveraged_components: List[ossp.SystemComponent], sample_ssp_path: str) -> None:
    """Test that a leveraged authorization is created."""
    leverager = Leverager(sample_leveraged_components, sample_ssp_path)
    result = leverager._create_leveraged_authz(sample_ssp_path)
    assert isinstance(result, ossp.LeveragedAuthorization)
    assert result.links[0].href == sample_ssp_path  # type: ignore
    assert result.title


def test_create_leveraging_components(
    sample_leveraged_components: List[ossp.SystemComponent], sample_ssp_path: str
) -> None:
    """Test that leveraging components are created."""
    leverager = Leverager(sample_leveraged_components, sample_ssp_path)
    result = leverager._create_leveraging_components()
    assert isinstance(result, list)
    assert all(isinstance(comp, ossp.SystemComponent) for comp in result)


def test_add_leveraged_info(
    sample_leveraging_ssp: ossp.SystemSecurityPlan,
    sample_leveraged_components: List[ossp.SystemComponent],
    sample_ssp_path: str
) -> None:
    """Test that leveraged information is added to the SSP."""
    leverager = Leverager(sample_leveraged_components, sample_ssp_path)
    leverager.add_leveraged_info(sample_leveraging_ssp)
    assert sample_leveraging_ssp.system_implementation.components is not None
    assert len(sample_leveraging_ssp.system_implementation.components) == 3
