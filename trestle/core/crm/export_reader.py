# Copyright (c) 2021 IBM Corp. All rights reserved.
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
"""Provided interface to read inheritance statements from Markdown."""
import os
import logging
import pathlib
import uuid
from typing import Dict, List, Tuple, Optional

from trestle.common.list_utils import as_list

import trestle.oscal.ssp as ossp
from trestle.core.crm.leveraged_statements import InheritanceMarkdownReader

logger = logging.getLogger(__name__)

# For each file in the inheritance markdown dir
##


class ExportReader:

    def __init__(self, ipath: pathlib.Path, ssp: ossp.SystemSecurityPlan):
        """
        Initialize export reader.

        Arguments:
            root_path: A root path object where an SSP's inheritance markdown is located.
            ssp: A system security plan with exports
        """
        self._ssp: ossp.SystemSecurityPlan = ssp
        self._ipath = ipath

    def read_inheritance(self) -> ossp.SystemSecurityPlan:
        # Get the implemented requirements from the leveraging SSP
        # Create dict of component title to component uuid of the components in the leveraging ssp
        # Create a dict of dict where the top level key is a string that is the control_id or statement_id and the subdictionary key is the leveraging component uuid and the value will be a tuple with inherited and satisfied statements
        # For each leveraged component
        ## Save the control directory information into dictionary
        ## For each control directory read the markdown
        ### For each md file, with the tuple returned form the processor, lookup the component uuid from the component name, add component uuid + leveraged info to dict.
        ## for ea

        impl_requirements: List[ossp.ImplementedRequirement] = self._ssp.control_implementation.implemented_requirements

        markdown_dict: Dict[str, Dict[uuid.UUID, Tuple[List[ossp.Inherited], List[ossp.Satisfied]]]] = {}

        uuid_by_title: Dict[str, uuid.UUID] = {}
        for component in as_list(self._ssp.system_implementation.components):
            uuid_by_title[component.title] = component.uuid

        for comp_dir in os.listdir(self._ipath):
            # print comp_dir variable to stdout
            for control_dir in os.listdir(self._ipath.joinpath(comp_dir)):
                control_dict: Dict[uuid.UUID, Tuple[List[ossp.Inherited], List[ossp.Satisfied]]] = {}
                if control_dir in markdown_dict:
                    control_dict = markdown_dict[control_dir]
                for file in os.listdir(self._ipath.joinpath(comp_dir, control_dir)):
                    reader = InheritanceMarkdownReader(self._ipath.joinpath(comp_dir, control_dir, file))
                    leveraged_info = reader.process_leveraged_statement_markdown()
                    if leveraged_info is None:
                        continue
                    for comp in leveraged_info[0]:
                        comp_uuid = uuid_by_title[comp]
                        inherited: List[ossp.Inherited] = []
                        satisfied: List[ossp.Satisfied] = []
                        if comp_uuid in control_dict:
                            inherited = control_dict[comp_uuid][0]
                            satisfied = control_dict[comp_uuid][1]

                        if leveraged_info[1] is not None:
                            inherited.append(leveraged_info[1])
                        if leveraged_info[2] is not None:
                            satisfied.append(leveraged_info[2])

                        control_dict[comp_uuid] = (inherited, satisfied)

                markdown_dict[control_dir] = control_dict

        # Merge all the implemented requirements in the SSP
        for implemented_requirement in as_list(impl_requirements):
            try:
                control_dict = markdown_dict[implemented_requirement.control_id]
                for by_comp in as_list(implemented_requirement.by_components):

                    # Might need to check if the lists are empty in the
                    # comp value
                    comp = control_dict[by_comp.uuid]

                    if by_comp.inherited is None:
                        by_comp.inherited = []

                    by_comp.inherited.extend(comp[0])

                    if by_comp.satisfied is None:
                        by_comp.satisfied = []

                    by_comp.inherited.extend(comp[0])

            except KeyError as e:
                # There is going to be a key error if we check on components
                # or statements that don't exist in the dictionary. You can check
                # in the top logic or handle it the thrown exception
                logger.debug(f'{e}')

            for stm in as_list(implemented_requirement.statements):
                statement_id = getattr(stm, 'statement_id', f'{implemented_requirement.control_id}_smt')
                try:
                    control_dict = markdown_dict[statement_id]
                    for by_comp in as_list(stm.by_components):

                        # Might need to check if the lists are empty in the
                        # comp value
                        comp = control_dict[by_comp.uuid]

                        if by_comp.inherited is None:
                            by_comp.inherited = []

                        by_comp.inherited.extend(comp[0])

                        if by_comp.satisfied is None:
                            by_comp.satisfied = []

                        by_comp.inherited.extend(comp[0])

                except KeyError as e:
                    # There is going to be a key error if we check on components
                    # or statements that don't exist in the dictionary. You can check
                    # in the top logic or handle it the thrown exception
                    logging.debug(f'{e}')

        self._ssp.control_implementation.implemented_requirements = impl_requirements
        return self._ssp
