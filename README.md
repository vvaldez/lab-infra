# Playbooks

### pb-apply-kvm.yml

Assumptions made:

- Can SSH in as root using private address.
- DNS is configured so redhat.com resolves.

### pb-apply-director.yml

Assumptions made:

- Can SSH in as root using private address.
- DNS is configured so redhat.com resolves.

# `ansible-inventory` Structure

```
ansible-inventory/
├── ibm/
│   ├── group_vars/
│   │   ├── all.yml
│   │   ├── gonzo.yml
|   |   └── kermit.yml
│   ├── hosts-gonzo
│   ├── hosts-kermit
│   └── templates/
│       ├── gonzo  (Datacenter specific input OSP templates)
│       └── kermit (Datacenter specific input OSP templates)
└── green/
    ├── group_vars/
    │   ├── all.yml
    │   ├── dev.yml
    │   └── test.yml
    ├── hosts-dev
    ├── hosts-test
    └── templates/
        └── .... (Datacenter specific input OSP templates)

```

# `ansible-playbooks` Structure

```
ansible-playbooks/
├── .vault_secret
├── .vault_secret.sample
├── ansible.cfg
├── generate-all-envs.sh
├── pb-generate-templates-locally.yml
├── pb-apply-director.yml
├── pb-apply-kvm.yml
├── README.md
├── ansible-generated/
│   └── green-dev/
│   │   └── ... (Output OSP templates)
│   └── green-test/
│   │   └── ... (Output OSP templates)
│   └── ibm-gonzo/
│   │   └── ... (Output OSP templates)
│   └── ibm-kermit/
│       └── ... (Output OSP templates)
└── roles/
    └── requirements.yml
```

# Goals

Refactor and demo out the structure to be used for `ansible-playbooks.git` and `ansible-inventory.git` for OpenStack deployments. Some key points to achieve:

- Allow for "standard" set of templates provided by `osp-templates` role
- "standard" set of templates should be overridable by environment specific templates in `ansible-inventory.git`
- Apply `director` role to Director server. This will configure from zero to `deploy.sh`
- Branching on the `ansible-playbooks.git` repository can be used to achieve `master`, `osp10`, `osp13`, `osp14` differences
- Only `master` branch is utilized on `ansible-inventory.git` repository. Different environments are contained to sub-folders.
- Configure a `test` environment in `ansible-inventory.git` that can be ran against a packaged Docker/Vagrant virtualized environment.

# Developer Workflow

Envisioned developer workflow goes as follows:

1. Developer pulls down `ansible-inventory.git:master` and `ansible-playbooks.git:master` repositories locally. (Or works on jumpbox)
2. Developer creates either a feature or personal branch to make changes.
3. Developer checks out new branch.
4. Developer makes changes to `ansible-inventory.git`/`ansible-playbooks.git`.
5. When satisfied, developer pushes changes to new branch.
6. Developer submits a pull request from new branch to `master` branch.
7. Lead approves/rejects pull requests. Repeat until steps 4 - 7 until necessary.
8. Master is always referenced as current, working, code.

# Notes

Generate playbook won't be added to Tower ... it's a developer action, not something that should/needs to be ran from Tower. `pb-install.yml`, etc,  can be added to Tower but it should use pre-generated templates from `ansible-generated/`. OpenStack Day-2 playbooks should be what becomes ran thru Tower.

# Known Issues

# Usage

### Installation

```sh
# Install Ansible Roles
ansible-galaxy install --role-file roles/requirements.yml

# Force the latest version of roles to be installed
ansible-galaxy install --role-file roles/requirements.yml --force
```

### Generating Output Templates Locally

```sh
# Include the inventory file of the environment to generate templates for using `-i path/to/hosts/file`
ansible-playbook -i ../ansible-inventory/ibm/hosts-kermit pb-generate-templates-locally.yml

# Quick mode will only generate templates that show up as changed by `git status`
ansible-playbook -i ../ansible-inventory/ibm/hosts-kermit pb-generate-templates-locally.yml -e quick=true

# Helper script to generate the templates for all environments
./generate-all-envs.sh
```

### Running KVM installation

```sh
# Include the inventory file of the environment to install using `-i path/to/hosts/file
ansible-playbook -i ../ansible-inventory/ibm/hosts-kermit --vault-password-file .vault_secret pb-apply-kvm.yml

# Enforce nic configration as well
ansible-playbook -i ../ansible-inventory/ibm/hosts-kermit --vault-password-file .vault_secret pb-apply-kvm.yml -e setup_nics=yes
```

### Running Director Installation

```sh
# Include the inventory file of the environment to install using `-i path/to/hosts/file`
ansible-playbook -i ../ansible-inventory/ibm/hosts-kermit pb-apply-director.yml

# Run only a certain numbered section(s) of the installation guide
# https://access.redhat.com/documentation/en-us/red_hat_openstack_platform/13/html-single/director_installation_and_usage/
ansible-playbook -i ../ansible-inventory/ibm/hosts-kermit pb-apply-director.yml --tags 4.1,4.2,4.3

# Enable debug mode for more verbose output
ansible-playbook -i ../ansible-inventory/ibm/hosts-kermit pb-apply-director.yml --tags 4.1 -e debug=true
```

### Tearing down existing Director

```sh
# Unregister Director from Satellite, destroy and undefine libvirt domain
ansible-playbook -i ../ansible-inventory/ibm/hosts-kermit pb-tear-down-env.yml --vault-password-file .vault_secret
```

# Ansible Vault

Ansible Vault is used to encrypt sensitive strings in the `ansible-inventory/` repository. `./vault_secret` in the `ansible-playbooks/` repository must contain the secret string to decrypt the sensitive strings:

```sh
echo '<secret string>' > ./vault_secret
```

The playbooks must be ran with `--vault-password-file ./vault_secret` as arguments

```sh
ansible-playbook -i ../ansible-inventory/blue/hosts-test pb-install-director.yml --vault-password-file ./vault_secret
```

### Generate a new vault string

1. Make sure the `./vault_secret` file is populated correctly

2. Generate the encrypted YAML key/value

  ```sh
  ansible-vault encrypt_string --vault-id .vault_secret --name 'key' 'secret_value'
  ```

### Encrypt SSL Key to place in `group_vars/` file

```sh
$ cat ssl-key
-----BEGIN RSA PRIVATE KEY-----
...
-----END RSA PRIVATE KEY-----

$ cat ssl-key | ansible-vault encrypt_string --vault-id ./vault_secret --name 'ssl_key'
Reading plaintext input from stdin. (ctrl-d to end input)
!vault |
          $ANSIBLE_VAULT;1.1;AES256
          ...
Encryption successful
```

### Decrypt individual keys

```
$ ansible-vault decrypt
Vault password:
Reading ciphertext input from stdin
$ANSIBLE_VAULT;1.1;AES256
37653465336131656562313865633336393566373832343534313839343966356633366162636163
6362643233363263633537376162343630663332343530630a363236313236653839313236323061
62313466613133326539613865336666633164393961343931353661373564343632393035613264
6266303235663565350a393662393062643738613837313166343066636363656231383334316261
6363
Decryption successful # (ctrl-d to end input)
unencrypted value here

$
```

## Ansible Vault Considerations for Input and Output Templates

The workflow for generating and syncing templates on the Director is such:

1. Populate variable files in `groups_vars/` in `ansible-inventory/` repo.
2. Generate output templates into `ansible-playbooks/ansible-generated/`
3. During a playbook run, re-template the files in `ansible-playbooks/ansible-generated/` into `/home/stack/ansible-generated/` on the director.

Input templates (from roles or inventory) and output templates in `ansible-playbooks/ansible-generated/` are commited into Git. This is a valuable feature, as it allows for changes to input templates, re-generation of output templates, and the quick ability to `diff` the generated templates to see how changes to the input affects the output.

Sensitive strings in the variables files are encrypted using Ansible Vault because they should not be tracked and human readable in Git, or even on the jumpbox itself. Additionally, we do not want the decrypted strings human readable within the output templates held in `ansible-playbooks/ansible-generated/`.

For this reason, decryption of sensitive strings **is not performed** during **step 2** above, where output templates get generated into `ansible-playbooks/ansible-generated/`. At this step we simply put the place holder for the variable into the output templates. Actual decryption of these senstive strings is **only** performed during **step 3**. The human-readable decrypted strings are then only placed onto the director box within `/home/stack/ansible-generated/`.

Example of an input template `instackenv.yml` utilizing an encrypted string (The actual Jinja2 variable substitution is [escaped](https://jinja.palletsprojects.com/en/2.10.x/templates/#escaping):

```yml
    pm_type: {{ instackenv.pm.type }}
    pm_user: {{ '{{' }} instackenv.pm.user }}
    pm_password: '{{ '{{' }} instackenv.pm.password }}'
```

Example of the generated output template in `ansible-playbooks/ansible-generated/instackenv.yml`:

```yml
    pm_type: pxe_ipmitool
    pm_user: {{ instackenv.pm.user }}
    pm_password: '{{ instackenv.pm.password }}'
```

Example of the final generated file on the directory within `/home/stack/ansible-generated/instackenv.yml`:

```yml
    pm_type: pxe_ipmitool
    pm_user: secret_user
    pm_password: 'secret_password'
```

Because decryption is only performed in **step 3**, that is the only step when it is necessary to pass in the decryption password using ``--vault-password-file ./vault_secret``.

# Coding Styleguide

## Ansible Variable Names

Use underscores for variable names. The Ansible docs explain what are [valid variable names](https://docs.ansible.com/ansible/latest/user_guide/playbooks_variables.html#creating-valid-variable-names)

```yaml
# Words seperated by underscores (_)
my_variable: foo
foo_bar_foo: bar
```

## `"` and `'`

```yml
key: 'static string'
key: "string with string interpolation {{ variable }}"
```

## Ansible Playbooks/Roles

- **Tasks** within **plays** or **blocks** are seperated by a single newline
- The last **task** in a play is followed by a single newline

- `hosts:` is always the first property defined for a **play**
- `tags:`, if used, is always placed as the last property defined for **plays**, **tasks**, or **blocks**

```yaml
- hosts: director
  name: 4.4 Registering and updating your undercloud
  vars:
    activation_key: "{{ redhat_satellite_director_ak }}"
  tasks:
    - name: Subscribe the system
      include_role:
        name: subscribe

    - name: yum update
      yum:
        name: '*'
        state: latest
      register: yum_output

    - name: Reboot
      reboot:
      when: yum_output.changed

  tags:
    - '4.4'
```

For readability, **plays** or **blocks** are always separated by 3 newlines:

```yaml
- hosts: director
  name: 4.5. Installing the director packages
  tasks:
    - name: Install python-tripleoclient
      shell: foo

  tags:
    - '4.5'



- hosts: director
  name: 4.6. Installing ceph-ansible
  tasks:
    - name: Enable the Ceph Tools repository
      shell: foo

  tags:
    - '4.6'



- hosts: director
  name: 4.6. Installing ceph-ansible
  tasks:
    - name: Enable the Ceph Tools repository
      shell: foo

  tags:
    - '4.7'
```

## YAML Indentation:

Indentation is always 2 spaces:

```yaml
overcloud:
  hostname: overcloud.exmaple.com
```

Always indent sequences:

```yaml
tasks:
  - foo: bar
  - bar:
    - item1
    - item2
```
