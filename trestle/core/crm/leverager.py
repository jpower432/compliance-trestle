# -*- mode:python; coding:utf-8 -*-
# Copyright (c) 2020 IBM Corp. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Reference authorizations and components from a leveraged SSP in a leveraging SSP."""

import logging
import os
import pathlib
from typing import List

import trestle.core.generators as gens
import trestle.oscal.common as common
import trestle.oscal.ssp as ossp
from trestle.common.list_utils import as_list

logger = logging.getLogger(__name__)


class Leverager():
    """Reference authorizations and components from a leveraged SSP in a leveraging SSP."""

    def __init__(self, leveraged_components: List[ossp.SystemComponent], ssp_path: pathlib.Path) -> None:
        """Initialize the Leverager class."""
        logger.debug('Initializing Leverager.')
        self._leveraged_components: List[ossp.SystemComponent] = leveraged_components
        self._leveraged_authz: ossp.LeveragedAuthorization = self._create_leveraged_authz(ssp_path)
        self._leveraging_components: List[ossp.SystemComponent] = self._create_leveraging_components()

    def _create_leveraged_authz(self, ssp_path: pathlib.Path) -> ossp.LeveragedAuthorization:
        """Create leveraged authorizations."""
        logger.debug('Creating leveraged authorizations.')
        leveraged_authz = gens.generate_sample_model(ossp.LeveragedAuthorization)
        # Insert the relative leveraged ssp path as a link
        leveraged_authz.links = []
        link: common.Link = common.Link(href=ssp_path)
        leveraged_authz.links.append(link)

        # Set the title of the leveraged authorization
        directory = os.path.dirname(ssp_path)
        leveraged_ssp = os.path.basename(directory)

        leveraged_authz.title = f'Leveraged Authorization for {leveraged_ssp}'
        return leveraged_authz

    def _create_leveraging_components(self) -> List[ossp.SystemComponent]:
        """Create leveraging components."""
        leveraging_components: List[ossp.SystemComponent] = []
        logger.debug('Creating leveraging components.')
        for comp in self._leveraged_components:

            leveraging_comp = gens.generate_sample_model(ossp.SystemComponent)
            leveraging_comp.type = comp.type
            leveraging_comp.title = comp.title
            leveraging_comp.description = comp.description
            leveraging_comp.status = comp.status

            leveraging_comp.props = []
            leveraging_comp.props.append(common.Property(name='implementation-point', value='external'))
            leveraging_comp.props.append(
                common.Property(name='leveraged-authorization-uuid', value=self._leveraged_authz.uuid)
            )
            leveraging_comp.props.append(common.Property(name='inherited-uuid', value=comp.uuid))
            # Add the leveraging component to the leveraging components list
            leveraging_components.append(leveraging_comp)

        return leveraging_components

    def add_leveraged_info(self, leveraging_ssp: ossp.SystemSecurityPlan) -> None:
        """Add leveraged information to the SSP."""
        logger.debug('Adding leveraged information.')
        leveraged_auths = as_list(leveraging_ssp.system_implementation.leveraged_authorizations)
        # Add the leveraged authorization to the leveraging SSP
        leveraging_ssp.system_implementation.leveraged_authorizations = leveraged_auths
        leveraging_ssp.system_implementation.leveraged_authorizations.append(self._leveraged_authz)
        # Add the leveraging components to the leveraging SSP
        leveraging_ssp.system_implementation.components = as_list(leveraging_ssp.system_implementation.components)
        leveraging_ssp.system_implementation.components = self._leveraging_components
