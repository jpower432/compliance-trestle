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
"""API for updating inheritance information in SSPs."""

import logging
import pathlib
from typing import List, Optional

import trestle.core.generators as gens
import trestle.oscal.common as common
import trestle.oscal.ssp as ossp
from trestle.common.err import TrestleError
from trestle.common.list_utils import as_list
from trestle.core.catalog.catalog_api import CatalogAPI
from trestle.core.crm.export_reader import ExportReader
from trestle.core.crm.export_writer import ExportWriter
from trestle.core.remote.cache import FetcherFactory

logger = logging.getLogger(__name__)


class SSPInheritanceAPI():
    """API for updating inheritance information in SSPs through inheritance markdown."""

    def __init__(self, inheritance_md_path: pathlib.Path, trestle_root: pathlib.Path) -> None:
        """Initialize the SSP Inheritance API class."""
        self._inheritance_markdown_path: pathlib.Path = inheritance_md_path
        self._trestle_root: pathlib.Path = trestle_root

    def write_inheritance_as_markdown(
        self, leveraged_ssp_reference: str, catalog_api: Optional[CatalogAPI] = None
    ) -> None:
        """
        Write inheritance information to markdown.

        Args:
            leveraged_ssp: SSP to write inheritance information from.
            catalog_api: Catalog API to filter inheritance information by catalog.

        Notes:
            If a catalog API is provided, the written controls in the markdown will be filtered by the catalog.
        """
        fetcher = FetcherFactory.get_fetcher(self._trestle_root, leveraged_ssp_reference)
        leveraged_ssp: ossp.SystemSecurityPlan
        try:
            leveraged_ssp, _ = fetcher.get_oscal()
        except TrestleError as e:
            raise TrestleError(f'Unable to fetch ssp from {leveraged_ssp_reference}: {e}')

        if catalog_api is not None:
            control_imp: ossp.ControlImplementation = leveraged_ssp.control_implementation

            new_imp_requirements: List[ossp.ImplementedRequirement] = []
            for imp_requirement in as_list(control_imp.implemented_requirements):
                control = catalog_api._catalog_interface.get_control(imp_requirement.control_id)
                if control is not None:
                    new_imp_requirements.append(imp_requirement)
            control_imp.implemented_requirements = new_imp_requirements

            leveraged_ssp.control_implementation = control_imp

        export_writer: ExportWriter = ExportWriter(
            self._inheritance_markdown_path, leveraged_ssp, leveraged_ssp_reference
        )
        export_writer.write_exports_as_markdown()

    def update_ssp_inheritance(self, ssp: ossp.SystemSecurityPlan) -> None:
        """
        Update inheritance information in SSP.

        Args:
            ssp: SSP to update with inheritance information.
        """
        logger.debug('Reading inheritance information from markdown.')
        reader = ExportReader(self._inheritance_markdown_path, ssp)
        ssp = reader.read_exports_from_markdown()

        # Reader get reference
        leveraged_ssp_reference = reader.get_leveraged_ssp_href()

        fetcher = FetcherFactory.get_fetcher(self._trestle_root, leveraged_ssp_reference)
        leveraged_ssp: ossp.SystemSecurityPlan
        try:
            leveraged_ssp, _ = fetcher.get_oscal()
        except TrestleError as e:
            raise TrestleError(f'Unable to fetch ssp from {leveraged_ssp_reference}: {e}')

        # If the export reader is None, this mean no component are mapped and this should be empty
        components: List[ossp.SystemComponent] = []
        leveraged_components = reader.get_leveraged_components()
        for component in as_list(leveraged_ssp.system_implementation.components):
            if component.title in leveraged_components:
                components.append(component)

        leveraged_authz = gens.generate_sample_model(ossp.LeveragedAuthorization)
        leveraged_authz.links = as_list(leveraged_authz.links)
        link: common.Link = common.Link(href=leveraged_ssp_reference)
        leveraged_authz.links.append(link)

        # Set the title of the leveraged authorization
        leveraged_authz.title = f'Leveraged Authorization for {leveraged_ssp.metadata.title}'

        leveraged_auths = as_list(ssp.system_implementation.leveraged_authorizations)
        # Add the leveraged authorization to the leveraging SSP
        ssp.system_implementation.leveraged_authorizations = leveraged_auths
        ssp.system_implementation.leveraged_authorizations.append(leveraged_authz)

        leveraging_components: List[ossp.SystemComponent] = []
        for comp in components:
            leveraging_comp = gens.generate_sample_model(ossp.SystemComponent)
            leveraging_comp.type = comp.type
            leveraging_comp.title = comp.title
            leveraging_comp.description = comp.description
            leveraging_comp.status = comp.status

            leveraging_comp.props = []
            leveraging_comp.props.append(common.Property(name='implementation-point', value='external'))
            leveraging_comp.props.append(
                common.Property(name='leveraged-authorization-uuid', value=leveraged_authz.uuid)
            )
            leveraging_comp.props.append(common.Property(name='inherited-uuid', value=comp.uuid))
            # Add the leveraging component to the leveraging components list
            leveraging_components.append(leveraging_comp)

        ssp.system_implementation.components = as_list(ssp.system_implementation.components)
        ssp.system_implementation.components.extend(leveraging_components)
