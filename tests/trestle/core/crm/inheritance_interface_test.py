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
"""Tests for the InheritanceInterface class."""

from tests import test_utils

import trestle.core.generators as gens
import trestle.oscal.ssp as ossp
from trestle.core.crm.inheritance_interface import InheritanceInterface

test_provided_uuid = '18ac4e2a-b5f2-46e4-94fa-cc84ab6fe114'
test_responsibility_uuid = '4b34c68f-75fa-4b38-baf0-e50158c13ac2'


def test_reconcile_inheritance_by_component() -> None:
    """Test retrieving isolated responsibilities statements."""
    by_comp: ossp.ByComponent = test_utils.generate_test_by_comp()
    by_comp.inherited = []
    by_comp.satisfied = []

    # Set up default inherited and satisfied statements
    inherited = gens.generate_sample_model(ossp.Inherited)
    inherited.provided_uuid = test_provided_uuid
    inherited.description = 'inherited description'
    satisfied = gens.generate_sample_model(ossp.Satisfied)
    satisfied.responsibility_uuid = test_responsibility_uuid
    satisfied.description = 'satisfied description'

    by_comp.inherited.append(inherited)
    by_comp.satisfied.append(satisfied)

    inheritance_interface: InheritanceInterface = InheritanceInterface(by_comp)

    # Create new inherited and satisfied statements and update the description
    new_inherited = gens.generate_sample_model(ossp.Inherited)
    new_inherited.provided_uuid = test_provided_uuid
    new_inherited.description = 'new inherited description'
    new_satisfied = gens.generate_sample_model(ossp.Satisfied)
    new_satisfied.responsibility_uuid = test_responsibility_uuid
    new_satisfied.description = 'new satisfied description'

    result_by_comp = inheritance_interface.reconcile_inheritance_by_component([new_inherited], [new_satisfied])

    # Ensure that the resulting by_component has one of each statement and the uuids match the originals
    assert len(result_by_comp.inherited) == 1
    assert len(result_by_comp.satisfied) == 1
    assert result_by_comp.inherited[0].uuid == inherited.uuid  # type: ignore
    assert result_by_comp.satisfied[0].uuid == satisfied.uuid  # type: ignore
    assert result_by_comp.inherited[0].description == new_inherited.description  # type: ignore
    assert result_by_comp.satisfied[0].description == new_satisfied.description  # type: ignore
