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
module: ome_user
short_description: Create, modify or delete a user on OpenManage Enterprise.
version_added: "2.9"
description: This module creates, modifies or deletes a user on OpenManage Enterprise.
options:
  hostname:
    description: Target IP Address or hostname.
    type: str
    required: true
  username:
    description: Target username.
    type: str
    required: true
  password:
    description: Target user password.
    type: str
    required: true
  port:
    description: Target HTTPS port.
    type: int
    default: 443
  state:
    type: str
    description:
      - C(present) creates a user in case the I(UserName) provided inside I(attributes) does not exist.
      - C(present) modifies a user in case the I(UserName) provided inside I(attributes) exists.
      - C(absent) deletes an existing user.
    choices: [present, absent]
    default: present
  user_id:
    description:
      - Unique ID of the user to be deleted.
      - Either I(user_id) or I(name) is mandatory for C(absent) operation.
    type: int
  name:
    type: str
    description:
      - Unique Name of the user to be deleted.
      - Either I(user_id) or I(name) is mandatory for C(absent) operation.
  attributes:
    type: dict
    default: {}
    description:
      - >-
        Payload data for the user operations. It can take the following attributes for C(present).
      - >-
        UserTypeId, DirectoryServiceId, Description, Name, Password, UserName, RoleId, Locked, Enabled.
      - >-
        OME will throw error if required parameter is not provided for operation.
      - >-
        Refer OpenManage Enterprise API Reference Guide for more details.
requirements:
    - "python >= 2.7.5"
author: "Sajna Shetty(@Sajna-Shetty)"
'''

EXAMPLES = r'''
---
- name: create user with required parameters.
  ome_user:
    hostname: "192.168.0.1"
    username: "username"
    password: "password"
    attributes:
      UserName: "user1"
      Password: "UserPassword"
      RoleId: "10"
      Enabled: True

- name: create user with all parameters.
  ome_user:
    hostname: "192.168.0.1"
    username: "username"
    password: "password"
    attributes:
      UserName: "user2"
      Description: "user2 description"
      Password: "UserPassword"
      RoleId: "10"
      Enabled: True
      DirectoryServiceId: 0
      UserTypeId: 1
      Locked: False
      Name: "user2"

- name: modify existing user.
  ome_user:
    hostname: "192.168.0.1"
    username: "username"
    password: "password"
    state: "present"
    attributes:
      UserName: "user3"
      RoleId: "10"
      Enabled: True
      Description: "Modify user Description"

- name: delete existing user using id.
  ome_user:
    hostname: "192.168.0.1"
    username: "username"
    password: "password"
    state: "absent"
    user_id: 1234

- name: delete existing user using name.
  ome_user:
    hostname: "192.168.0.1"
    username: "username"
    password: "password"
    state: "absent"
    name: "name"
'''

RETURN = r'''
---
msg:
  description: Overall status of the user operation.
  returned: always
  type: str
  sample: "Successfully created a User"
user_status:
  description: Details of the user operation, when I(state) is C(present).
  returned: When I(state) is C(present).
  type: dict
  sample:
    {
        "Description": "Test user creation",
        "DirectoryServiceId": 0,
        "Enabled": true,
        "Id": "61546",
        "IsBuiltin": false,
        "Locked": false,
        "Name": "test",
        "Password": null,
        "PlainTextPassword": null,
        "RoleId": "10",
        "UserName": "test",
        "UserTypeId": 1
    }
'''

import json
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.remote_management.dellemc.ome import RestOME
from ansible.module_utils.six.moves.urllib.error import URLError, HTTPError
from ansible.module_utils.urls import ConnectionError, SSLValidationError


def _validate_inputs(module):
    """both user_id and name are not acceptable in case of state is absent"""
    state = module.params['state']
    user_id = module.params.get('user_id')
    name = module.params.get('name')
    if state != 'present' and (user_id is None and name is None):
        fail_module(module, msg="One of the following 'user_id' or 'name' "
                                "option is required for state 'absent'")


def get_user_id_from_name(rest_obj, name):
    """Get the account id using account name"""
    user_id = None
    if name is not None:
        resp = rest_obj.invoke_request('GET', 'AccountService/Accounts')
        if resp.success:
            for user in resp.json_data.get('value'):
                if 'UserName' in user and user['UserName'] == name:
                    return user['Id']
    return user_id


def _get_resource_parameters(module, rest_obj):
    state = module.params["state"]
    payload = module.params.get("attributes")
    if state == "present":
        name = payload.get('UserName')
        user_id = get_user_id_from_name(rest_obj, name)
        if user_id is not None:
            payload.update({"Id": user_id})
            path = "AccountService/Accounts('{user_id}')".format(user_id=user_id)
            method = 'PUT'
        else:
            path = "AccountService/Accounts"
            method = 'POST'
    else:
        user_id = module.params.get("user_id")
        if user_id is None:
            name = module.params.get('name')
            user_id = get_user_id_from_name(rest_obj, name)
            if user_id is None:
                fail_module(module, msg="Unable to get the account because the specified account "
                                        "does not exist in the system.")
        path = "AccountService/Accounts('{user_id}')".format(user_id=user_id)
        method = 'DELETE'
    return method, path, payload


def password_no_log(attributes):
    if isinstance(attributes, dict) and 'Password' in attributes:
        attributes['Password'] = "VALUE_SPECIFIED_IN_NO_LOG_PARAMETER"


def fail_module(module, **failmsg):
    password_no_log(module.params.get("attributes"))
    module.fail_json(**failmsg)


def exit_module(module, response, http_method):
    password_no_log(module.params.get("attributes"))
    msg_dict = {'POST': "Successfully created a User",
                'PUT': "Successfully modified a User",
                'DELETE': "Successfully deleted the User"}
    state_msg = msg_dict[http_method]
    if response.status_code != 204:
        module.exit_json(msg=state_msg, changed=True, user_status=response.json_data)
    else:
        # For delete operation no response content is returned
        module.exit_json(msg=state_msg, changed=True)


def main():
    module = AnsibleModule(
        argument_spec={
            "hostname": {"required": True, "type": 'str'},
            "username": {"required": True, "type": 'str'},
            "password": {"required": True, "type": 'str', "no_log": True},
            "port": {"required": False, "default": 443, "type": 'int'},
            "state": {"required": False, "type": 'str', "default": "present",
                      "choices": ['present', 'absent']},
            "user_id": {"required": False, "type": 'int'},
            "name": {"required": False, "type": 'str'},
            "attributes": {"required": False, "type": 'dict'},
        },
        mutually_exclusive=[['user_id', 'name'], ],
        required_if=[['state', 'present', ['attributes']], ],
        supports_check_mode=False)

    try:
        _validate_inputs(module)
        if module.params.get("attributes") is None:
            module.params["attributes"] = {}
        with RestOME(module.params, req_session=True) as rest_obj:
            method, path, payload = _get_resource_parameters(module, rest_obj)
            resp = rest_obj.invoke_request(method, path, data=payload)
            if resp.success:
                exit_module(module, resp, method)
    except HTTPError as err:
        fail_module(module, msg=str(err), user_status=json.load(err))
    except (URLError, SSLValidationError, ConnectionError, TypeError, ValueError) as err:
        fail_module(module, msg=str(err))


if __name__ == '__main__':
    main()
