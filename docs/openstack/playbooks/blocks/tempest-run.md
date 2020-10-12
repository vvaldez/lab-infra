# Ansible Playbook: Tempest run

This playbook will:

- If `{{ remove }}` is `true` then delete any existing Tempest workspace found at `/home/stack/tempest/tempest-{{ site_name }}`
- If there is not an existing Tempest workspace named `tempest-{{ site_name }}`, then:
  - Initialize the Tempest workspace named `tempest-{{ site_name }}`
  - Source `/home/stack/{{ site_name }}rc` and grab the Neutron network UUID of `{{ network_name }}`
  - Generate the initial `tempest.conf` file using `discover-tempest-config`
  - Modify the generated `tempest.conf` file with `crudini` to match working settings
  - Download the RHEL7 qcow2 to use for launching instances, if it does not already exist
  - If any of the above steps fail, delete the non-functional Tempest workspace `tempest-{{ site_name }}`
- Create `/home/stack/ansible-generated-logs` if it does not exist
- Initialize a tempest saved state using `tempest cleanup --init-saved-state`
- Run Tempest smoke tests
- Generate the HTML output into `/home/stack/ansible-generated-logs/tempest-{{ id }}.html`. `{{ id }}` is an autogenerated ID number for the Tempest run.
- Show the brief results of the Tempest run in a debug statement

## Usage

The following is an example run of the playbook using Ansible CLI.

**Note:** Always run the playbook from the top level directory of `ansible-playbook`

```yml
- name: Tempest run
  import_playbook: ../blocks/tempest-run.yml
  vars:
    site_name: central
    network_name: management-central-net
```

## Requirements

The following requirements need to be met.

- The following file exists: `/home/stack/images/rhel-server-7.7-x86_64-kvm.qcow2`
- If the above file does not exist, it will attempt to be downloaded from: `http://{{ hostvars[groups['infra'][0]].ansible_host }}/rhel7/isos/rhel-server-7.7-x86_64-kvm.qcow2`

## Playbook variables

The following variables are required to be set.

| Variable | Type | Description |
| -------- | ---- | ----------- |
| `site_name` | string | The name of the Tempest workspace to create. The workspace created will be named `tempest-{{ site_name }`
| `network_name` | string | The name of the Neutron network to use for testing

The following variables can be optionally set, and have default values, if not set.

| Variable | Type | Default | Description |
| -------- | ---- | ------- | ----------- |
| `remove` | bool | `false` | If this is set to true, remove any existing tempest workspace named `tempest-{{ site_name }}` and also remove any directory existing at `/home/stack/tempest-{{ site_name }}`
| `concurrency` | int | `0` | The value to use for concurrency of tests ran. When the value is set to 0, Tempest uses it's default value which is the number of system CPUs

## Inventory requirements

There are no inventory requirements.