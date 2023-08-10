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
"""Tests for the ssp_generator module."""

import argparse
import pathlib
import os

from _pytest.monkeypatch import MonkeyPatch

from tests import test_utils
from tests.test_utils import FileChecker, setup_for_ssp

import trestle.core.crm.export_reader as exportreader
import trestle.core.generators as gens
import trestle.core.generic_oscal as generic
import trestle.oscal.profile as prof
import trestle.oscal.ssp as ossp
from trestle.common import const, file_utils, list_utils
from trestle.common.model_utils import ModelUtils
from trestle.core.commands.author.ssp import SSPAssemble, SSPFilter, SSPGenerate
from trestle.core.control_context import ContextPurpose, ControlContext
from trestle.core.control_reader import ControlReader
from trestle.core.markdown.markdown_api import MarkdownAPI
from trestle.core.models.file_content_type import FileContentType
from trestle.core.profile_resolver import ProfileResolver

leveraged_ssp = 'leveraged_ssp'
leveraging_ssp = 'my_ssp'

expected_uuid = '22222222-0000-4000-9001-000000000003'

inheritance_text = """---
x-trestle-statement:
  # Add or modify leveraged SSP Statements here.
  provided-uuid: 18ac4e2a-b5f2-46e4-94fa-cc84ab6fe114
  responsibility-uuid: 4b34c68f-75fa-4b38-baf0-e50158c13ac2
x-trestle-leveraging-comp:
  # Leveraged statements can be optionally associated with components in this system.
  # Associate leveraged statements to Components of this system here:
  - name: Access Control Appliance
---

# Provided Statement Description

provided statement description

# Responsibility Statement Description

resp statement description

# Satisfied Statement Description

<!-- Use this section to explain how the inherited responsibility is being satisfied. -->
My Satisfied Description
"""


def test_exports_reader(tmp_trestle_dir: pathlib.Path) -> None:
    """Test ssp-generate with inheritance view."""
    ipath = tmp_trestle_dir.joinpath(leveraging_ssp, const.INHERITANCE_VIEW_DIR)
    this_system_dir = ipath.joinpath('Access Control Appliance')
    ac_21 = this_system_dir.joinpath('ac-2')
    ac_21.mkdir(parents=True)

    file = ac_21 / f'{expected_uuid}.md'
    f = open(file, "w")
    f.write(inheritance_text)
    f.close()

    test_utils.load_from_json(
        tmp_trestle_dir, 'leveraging_ssp', leveraging_ssp, ossp.SystemSecurityPlan
    )  # type: ignore

    orig_ssp, _ = ModelUtils.load_model_for_class(tmp_trestle_dir, leveraging_ssp, ossp.SystemSecurityPlan, FileContentType.JSON)

    reader = exportreader.ExportReader(ipath, orig_ssp)  # type: ignore
    ssp = reader.read_inheritance()

    for c in ssp.control_implementation.implemented_requirements:
        if c.control_id == 'ac-2':
            if c.by_components is not None:
                for comp in c.by_components:
                    if comp.component_uuid == expected_uuid:
                        if comp.inherited is not None:
                            for inherited in comp.inherited:
                                assert inherited.provided_uuid == '18ac4e2a-b5f2-46e4-94fa-cc84ab6fe114'
                        if comp.satisfied is not None:
                            for responsibility in comp.satisfied:
                                assert responsibility.responsibility_uuid == '4b34c68f-75fa-4b38-baf0-e50158c13ac2'
                                assert responsibility.description == 'My Satisfied Description'
