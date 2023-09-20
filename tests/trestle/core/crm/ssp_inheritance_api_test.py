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
"""Tests for SSP Inheritance API."""

import logging
import pathlib

from tests import test_utils

import trestle.oscal.ssp as ossp
from trestle.common import const
from trestle.common.model_utils import ModelUtils
from trestle.core.crm.ssp_inheritance_api import SSPInheritanceAPI
from trestle.core.models.file_content_type import FileContentType

logger = logging.getLogger(__name__)

leveraging_ssp = 'my_ssp'
leveraged_ssp = 'leveraged_ssp'

inheritance_text = """---
x-trestle-statement:
  # Add or modify leveraged SSP Statements here.
  provided-uuid: 18ac4e2a-b5f2-46e4-94fa-cc84ab6fe115
  responsibility-uuid: 4b34c68f-75fa-4b38-baf0-e50158c13ac3
x-trestle-leveraging-comp:
  # Leveraged statements can be optionally associated with components in this system.
  # Associate leveraged statements to Components of this system here:
  - name: Access Control Appliance
x-trestle-global:
    leveraged-ssp:
      href: trestle://system-security-plans/leveraged_ssp/system-security-plan.json
---

# Provided Statement Description

provided statement description

# Responsibility Statement Description

resp statement description

# Satisfied Statement Description

<!-- Use this section to explain how the inherited responsibility is being satisfied. -->
"""

expected_appliance_uuid = '22222222-0000-4000-9001-000000000003'


def test_update_ssp_inheritance(tmp_trestle_dir: pathlib.Path) -> None:
    """Test that a leveraged authorization is created."""
    inheritance_path = tmp_trestle_dir.joinpath(leveraged_ssp, const.INHERITANCE_VIEW_DIR)
    ac_appliance_dir = inheritance_path.joinpath('Access Control Appliance')
    ac_2 = ac_appliance_dir.joinpath('ac-2')
    ac_2.mkdir(parents=True)

    file = ac_2 / f'{expected_appliance_uuid}.md'
    with open(file, 'w') as f:
        f.write(inheritance_text)

    # test with a statement
    ac_2a = ac_appliance_dir.joinpath('ac-2_smt.a')
    ac_2a.mkdir(parents=True)

    file = ac_2a / f'{expected_appliance_uuid}.md'
    with open(file, 'w') as f:
        f.write(inheritance_text)

    test_utils.load_from_json(tmp_trestle_dir, 'leveraged_ssp', leveraged_ssp, ossp.SystemSecurityPlan)
    test_utils.load_from_json(tmp_trestle_dir, 'leveraging_ssp', leveraging_ssp, ossp.SystemSecurityPlan)

    orig_ssp, _ = ModelUtils.load_model_for_class(
        tmp_trestle_dir,
        leveraging_ssp,
        ossp.SystemSecurityPlan,
        FileContentType.JSON)

    ssp_inheritance_api = SSPInheritanceAPI(inheritance_path, tmp_trestle_dir)
    ssp_inheritance_api.update_ssp_inheritance(orig_ssp)

    assert orig_ssp.system_implementation.leveraged_authorizations is not None
    # There is two because the original document has an existing leveraged authorization
    assert len(orig_ssp.system_implementation.leveraged_authorizations) == 2

    auth = orig_ssp.system_implementation.leveraged_authorizations[1]

    assert auth.links is not None
    assert len(auth.links) == 1
    assert auth.links[0].href == 'trestle://system-security-plans/leveraged_ssp/system-security-plan.json'
