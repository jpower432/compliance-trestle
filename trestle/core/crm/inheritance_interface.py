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
"""Provide interface to ssp allowing queries and operations for inherited and satisfied statements."""

import copy
import logging
from typing import Dict, List

import trestle.oscal.ssp as ossp
from trestle.common.list_utils import as_list, none_if_empty

logger = logging.getLogger(__name__)


class InheritanceInterface:
    """Interface to update inherited and satisfied statements in a by-component assembly."""

    def __init__(self, by_comp: ossp.ByComponent):
        """Initialize inheritance writer for a single by-component assembly."""
        self._by_comp: ossp.ByComponent = by_comp
        # uuid is provided uuid
        self._inherited_dict: Dict[str, ossp.Inherited] = self._create_inherited_dict()
        # uuid is responsibility uuid
        self._satisfied_dict: Dict[str, ossp.Satisfied] = self._create_satisfied_dict()

    def _create_inherited_dict(self) -> Dict[str, ossp.Inherited]:
        inherited_dict: Dict[str, ossp.Inherited] = {}
        for inherited in as_list(self._by_comp.inherited):
            inherited_dict[str(inherited.provided_uuid)] = inherited
        return inherited_dict

    def _create_satisfied_dict(self) -> Dict[str, ossp.Satisfied]:
        satisfied_dict: Dict[str, ossp.Satisfied] = {}
        for satisfied in as_list(self._by_comp.satisfied):
            satisfied_dict[str(satisfied.responsibility_uuid)] = satisfied
        return satisfied_dict

    def reconcile_inheritance_by_component(
        self, incoming_inherited: List[ossp.Inherited], incoming_satisfied: List[ossp.Satisfied]
    ) -> ossp.ByComponent:
        """
        Reconcile the inherited and satisfied statements in the by-component assembly with changes from the export.

        Notes:
            A statement is determined as existing if the provided uuid or responsibility uuid is in the existing in the
            by-component assembly. If existing, the description will be updated if it has changed.

            Any existing inherited or satisfied statements that are not in the incoming export will be removed.
            If a statement is in the incoming export, but not in the existing by-component assembly, it will be added.
        """
        new_inherited: List[ossp.Inherited] = []
        new_satisfied: List[ossp.Satisfied] = []

        # Create a copy of the input by-component assembly to reconcile and return
        new_by_comp: ossp.ByComponent = copy.deepcopy(self._by_comp)

        for statement in incoming_inherited:
            if statement.provided_uuid in self._inherited_dict:
                existing_statement = self._inherited_dict[str(statement.provided_uuid)]
                # Update the description if it has changed
                existing_statement.description = statement.description
                statement = existing_statement
            new_inherited.append(statement)

        new_by_comp.inherited = none_if_empty(new_inherited)

        for statement in incoming_satisfied:
            if statement.responsibility_uuid in self._satisfied_dict:
                existing_statement = self._satisfied_dict[str(statement.responsibility_uuid)]
                # Update the description if it has changed
                existing_statement.description = statement.description
                statement = existing_statement
            new_satisfied.append(statement)

        new_by_comp.satisfied = none_if_empty(new_satisfied)

        return new_by_comp
