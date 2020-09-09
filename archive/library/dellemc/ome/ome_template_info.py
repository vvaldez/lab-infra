#!/usr/bin/python
# -*- coding: utf-8 -*-

#
# Dell EMC OpenManage Ansible Modules
# Version 2.0.12
# Copyright (C) 2019-2020 Dell Inc. or its subsidiaries. All Rights Reserved.

# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
#


from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
module: ome_template_info
short_description: Retrieves template details from OpenManage Enterprise.
version_added: "2.9"
description:
   - This module retrieves the list and details of all the templates on OpenManage Enterprise.
options:
  hostname:
    description: Target IP address or hostname.
    type: str
    required: True
  username:
    description: Target username.
    type: str
    required: True
  password:
    description: Target user password.
    type: str
    required: True
  port:
    description: Target HTTPS port.
    type: int
    default: 443
  template_id:
    description: Unique Id of the template.
    type: int
  system_query_options:
    description: Options for pagination of the output.
    type: dict
    suboptions:
      filter:
        description: Filter records by the supported values.
        type: str
requirements:
    - "python >= 2.7.5"
author: "Sajna Shetty(@Sajna-Shetty)"

'''

EXAMPLES = r'''
---
- name: Retrieve basic details of all templates.
  ome_template_info:
    hostname: "192.168.0.1"
    username: "username"
    password: "password"

- name: Retrieve details of a specific template identified by its template ID.
  ome_template_info:
    hostname: "192.168.0.1"
    username: "username"
    password: "password"
    template_id: 1

- name: Get filtered template info based on name.
  ome_template_info:
    hostname: "192.168.0.1"
    username: "username"
    password: "password"
    system_query_options:
      filter: "Name eq 'new template'"
'''

RETURN = r'''
---
msg:
  type: str
  description: Over all template facts status.
  returned: on error
  sample: "Failed to fetch the template facts"
template_info:
  type: dict
  description: Details of the templates.
  returned: success
  sample: {
        "192.168.0.1": {
            "CreatedBy": "system",
            "CreationTime": "1970-01-31 00:00:56.372144",
            "Description": "Tune workload for Performance Optimized Virtualization",
            "HasIdentityAttributes": false,
            "Id": 1,
            "IdentityPoolId": 0,
            "IsBuiltIn": true,
            "IsPersistencePolicyValid": false,
            "IsStatelessAvailable": false,
            "LastUpdatedBy": null,
            "LastUpdatedTime": "1970-01-31 00:00:56.372144",
            "Name": "iDRAC Enable Performance Profile for Virtualization",
            "SourceDeviceId": 0,
            "Status": 0,
            "TaskId": 0,
            "TypeId": 2,
            "ViewTypeId": 4
        }
    }
'''

import json
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.remote_management.dellemc.ome import RestOME
from ansible.module_utils.six.moves.urllib.error import URLError, HTTPError
from ansible.module_utils.urls import ConnectionError, SSLValidationError


def _get_query_parameters(module_params):
    """Builds query parameter.

    :return: dict
    :example: {"$filter": Name eq 'template name'}
    """
    system_query_param = module_params.get("system_query_options")
    query_param = {}
    if system_query_param:
        query_param = {"$" + k: v for k, v in system_query_param.items() if v is not None}
    return query_param


def main():
    module = AnsibleModule(
        argument_spec={
            "hostname": {"required": True, "type": 'str'},
            "username": {"required": True, "type": 'str'},
            "password": {"required": True, "type": 'str', "no_log": True},
            "port": {"required": False, "type": 'int', "default": 443},
            "template_id": {"type": 'int', "required": False},
            "system_query_options": {"required": False, "type": 'dict',
                                     "options": {"filter": {"type": 'str', "required": False}}
                                     },
        },
        mutually_exclusive=[['template_id', 'system_query_options']],
        supports_check_mode=False
    )
    template_uri = "TemplateService/Templates"
    try:
        with RestOME(module.params, req_session=True) as rest_obj:
            query_param = None
            if module.params.get("template_id") is not None:
                # Fetch specific template
                template_id = module.params.get("template_id")
                template_path = "{0}({1})".format(template_uri, template_id)
            elif module.params.get("system_query_options") is not None:
                # Fetch all the templates based on Name
                query_param = _get_query_parameters(module.params)
                template_path = template_uri
            else:
                # Fetch all templates
                template_path = template_uri
            resp = rest_obj.invoke_request('GET', template_path, query_param=query_param)
            template_facts = resp.json_data
        if resp.status_code == 200:
            module.exit_json(template_info={module.params["hostname"]: template_facts})
        else:
            module.fail_json(msg="Failed to fetch the template facts")
    except HTTPError as err:
        module.fail_json(msg=json.load(err))
    except (URLError, SSLValidationError, ConnectionError, TypeError, ValueError) as err:
        module.fail_json(msg=str(err))


if __name__ == '__main__':
    main()
