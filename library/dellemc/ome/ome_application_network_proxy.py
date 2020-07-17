#!/usr/bin/python
# -*- coding: utf-8 -*-

#
# Dell EMC OpenManage Ansible Modules
# Version 2.0.12
# Copyright (C) 2020 Dell Inc. or its subsidiaries. All Rights Reserved.

# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
#


from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
module: ome_application_network_proxy
short_description: Updates the proxy configuration on OpenManage Enterprise.
version_added: "2.9"
description: This module allows to configure a network proxy on OpenManage Enterprise.
options:
  hostname:
    description: Target IP Address or hostname.
    required: true
    type: str
  username:
    description: Target username.
    required: true
    type: str
  password:
    description: Target user password.
    required: true
    type: str
  port:
    description: Target HTTPS port.
    default: 443
    type: int
  enable_proxy:
    description:
      - Enables or disables the HTTP proxy configuration.
      - If I(enable proxy) is false, then the HTTP proxy configuration is set to its default value.
    required: true
    type: bool
  ip_address:
    description:
      - Proxy server address.
      - This option is mandatory when I(enable_proxy) is true.
    type: str
  proxy_port:
    description:
      - Proxy server's port number.
      - This option is mandatory when I(enable_proxy) is true.
    type: int
  enable_authentication:
    description:
      - Enable or disable proxy authentication.
      - If I(enable_authentication) is true, I(proxy_username) and I(proxy_password) must be provided.
      - If I(enable_authentication) is false, the proxy username and password are set to its default values.
    required: false
    type: bool
  proxy_username:
    description:
      - Proxy server username.
      - This option is mandatory when I(enable_authentication) is true.
    required: false
    type: str
  proxy_password:
    description:
      - Proxy server password.
      - This option is mandatory when I(enable_authentication) is true.
    required: false
    type: str
requirements:
    - "python >= 2.7.5"
author:
    - "Sajna Shetty(@Sajna-Shetty)"
'''

EXAMPLES = r'''
---
- name: Update proxy configuration and enable authentication.
  ome_application_network_proxy:
    hostname: "192.168.0.1"
    username: "username"
    password: "password"
    enable_proxy: true
    ip_address: "192.168.0.2"
    proxy_port: 444
    enable_authentication: true
    proxy_username: "proxy_username"
    proxy_password: "proxy_password"

- name: Reset proxy authentication.
  ome_application_network_proxy:
    hostname: "192.168.0.1"
    username: "username"
    password: "password"
    enable_proxy: true
    ip_address: "192.168.0.2"
    proxy_port: 444
    enable_authentication: false

- name: Reset proxy configuration.
  ome_application_network_proxy:
    hostname: "192.168.0.1"
    username: "username"
    password: "password"
    enable_proxy: false
'''

RETURN = r'''
---
msg:
  type: str
  description: Overall status of the network proxy configuration change.
  returned: always
  sample: "Successfully updated network proxy configuration."
proxy_configuration:
  type: dict
  description: Updated application network proxy configuration.
  returned: success
  sample: {
        "EnableAuthentication": true,
        "EnableProxy": true,
        "IpAddress": "192.168.0.2",
        "Password": null,
        "PortNumber": 444,
        "Username": "root"
        }
error_info:
  description: Details of the HTTP error.
  returned: on HTTP error
  type: dict
  sample: {
        "error": {
            "@Message.ExtendedInfo": [
                {
                   "Message": "Unable to complete the request because the input value
                    for  PortNumber  is missing or an invalid value is entered.",
                    "MessageArgs": [
                        "PortNumber"
                    ],
                    "MessageId": "CGEN6002",
                    "RelatedProperties": [],
                    "Resolution": "Enter a valid value and retry the operation.",
                    "Severity": "Critical"
                }
            ],
            "code": "Base.1.0.GeneralError",
            "message": "A general error has occurred. See ExtendedInfo for more information."
        }
    }
'''

import json
from ssl import SSLError
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.remote_management.dellemc.ome import RestOME
from ansible.module_utils.urls import open_url, ConnectionError, SSLValidationError
from ansible.module_utils.six.moves.urllib.error import URLError, HTTPError

PROXY_CONFIG = "ApplicationService/Network/ProxyConfiguration"


def remove_unwanted_keys(key_list, payload):
    [payload.pop(key) for key in key_list if key in payload]


def get_payload(module):
    params = module.params
    proxy_payload_map = {
        "ip_address": "IpAddress",
        "proxy_port": "PortNumber",
        "enable_proxy": "EnableProxy",
        "proxy_username": "Username",
        "proxy_password": "Password",
        "enable_authentication": "EnableAuthentication"
    }
    backup_params = params.copy()
    remove_keys = ["hostname", "username", "password", "port"]
    remove_unwanted_keys(remove_keys, backup_params)
    payload = {proxy_payload_map[key]: val for key, val in backup_params.items() if val is not None}
    return payload


def get_updated_payload(rest_obj, module, payload):
    current_setting = {}
    if not any(payload):
        module.fail_json(msg="Unable to configure the proxy because proxy configuration settings are not provided.")
    else:
        params = module.params
        remove_keys = ["@odata.context", "@odata.type", "@odata.id", "Password"]
        enable_authentication = params.get("enable_authentication")
        if enable_authentication is False:
            """when enable auth is disabled, ignore proxy username and password """
            remove_keys.append("Username")
            payload.pop('Username', None)
            payload.pop('Password', None)
        resp = rest_obj.invoke_request("GET", PROXY_CONFIG)
        current_setting = resp.json_data
        remove_unwanted_keys(remove_keys, current_setting)
        diff = any(key in current_setting and val != current_setting[key] for key, val in payload.items())
        if not diff:
            module.exit_json(msg="No changes made to proxy configuration as entered values are the same as current configuration values.")
        else:
            current_setting.update(payload)
    return current_setting


def main():
    module = AnsibleModule(
        argument_spec={
            "hostname": {"required": True, "type": "str"},
            "username": {"required": True, "type": "str"},
            "password": {"required": True, "type": "str", "no_log": True},
            "port": {"required": False, "type": "int", "default": 443},
            "ip_address": {"required": False, "type": "str"},
            "proxy_port": {"required": False, "type": "int"},
            "enable_proxy": {"required": True, "type": "bool"},
            "proxy_username": {"required": False, "type": "str"},
            "proxy_password": {"required": False, "type": "str", "no_log": True},
            "enable_authentication": {"required": False, "type": "bool"},
        },
        required_if=[['enable_proxy', True, ['ip_address', 'proxy_port']],
                     ['enable_authentication', True, ['proxy_username', 'proxy_password']], ],
    )
    try:
        with RestOME(module.params, req_session=True) as rest_obj:
            payload = get_payload(module)
            updated_payload = get_updated_payload(rest_obj, module, payload)
            resp = rest_obj.invoke_request("PUT", PROXY_CONFIG, data=updated_payload)
            module.exit_json(msg="Successfully updated network proxy configuration.", proxy_configuration=resp.json_data,
                                 changed=True)
    except HTTPError as err:
        module.fail_json(msg=str(err), error_info=json.load(err))
    except URLError as err:
        module.exit_json(msg=str(err), unreachable=True)
    except (IOError, ValueError, SSLError, TypeError, ConnectionError, SSLValidationError) as err:
        module.fail_json(msg=str(err))
    except Exception as err:
        module.fail_json(msg=str(err))


if __name__ == "__main__":
    main()
