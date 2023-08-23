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
import uuid
from typing import Dict, List, Tuple

import trestle.oscal.ssp as ossp
from trestle.common.err import TrestleError
from trestle.common.list_utils import as_dict, as_list

logger = logging.getLogger(__name__)


class InheritanceInterface:
    """
    Interface to query exported inherited and satisfied statements from.

    The by-component export statement is parsed and the responsibility and provided statements
    are separated into three catagories:

    isolated responsibilities - A responsibility with no provided statement
    isolated provided - A provided statement with no referring responsibility statements
    export set - A set with a single responsibility and referred provided statement
    """

    def __init__(self, by_comp: ossp.ByComponent):
        """Initialize inheritance writer for a single by-component assembly."""
        self._by_comp: ossp.ByComponent = by_comp
        # uuid is provided uuid
        self._inherited_dict: Dict[uuid.UUID, ossp.Inherited] = self._create_inherited_dict()
        # uuid is responsibility uuid
        self._satisfied_dict: Dict[uuid.UUID, ossp.Satisfied] = self._create_satisfied_dict()

    def _create_inherited_dict(self) -> Dict[uuid.UUID, ossp.Inherited]:
        inherited_dict: Dict[uuid.UUID, ossp.Inherited] = {}
        for provided in as_list(self._by_comp.inherited):
            inherited_dict[provided.uuid] = provided
        return inherited_dict

    def _create_satisfied_dict(self) -> Dict[uuid.UUID, ossp.Satisfied]:
        satisfied_dict: Dict[uuid.UUID, ossp.Satisfied] = {}
        for responsibility in as_list(self._by_comp.satisfied):
            satisfied_dict[responsibility.uuid] = responsibility
        return satisfied_dict
    
    def reconcile_inheritance_by_component(self, incoming_inherited: List[ossp.Inherited], incoming_satisfied: List[ossp.Satisfied]) -> ossp.ByComponent:
        # This function checks an existing ssp for inherited and satisfied statements
        # if an inherited or satisfied statement exists with a matching
        # provided or responsibility uuid from markdown inheritance information,
        # that statement uuid is retained 

        # Replace self.by_comp.inherited with the reconciled

        new_inherited: List[ossp.Inherited] = []

        new_by_comp: ossp.ByComponent = copy.deepcopy(self._by_comp)

        for statement in incoming_inherited:
            if statement.provided_uuid in self._inherited_dict:
                statement.uuid = self._inherited_dict[uuid.UUID(statement.provided_uuid)].uuid
            new_inherited.append(statement)
        new_by_comp.inherited = new_inherited

        new_satisfied: List[ossp.Satisfied] = []

        for statement in incoming_satisfied:
            if statement.responsibility_uuid in self._satisfied_dict:
                statement.uuid = self._satisfied_dict[uuid.UUID(statement.responsibility_uuid)].uuid
            new_satisfied.append(statement)
        new_by_comp.satisfied = new_satisfied

        return new_by_comp

        
                    
        
