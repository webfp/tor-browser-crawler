Role Name
=========

A brief description of the role goes here.

Requirements
------------

Any pre-requisites that may not be covered by Ansible itself or the role should be mentioned here. For instance, if the role uses the EC2 module, it may be a good idea to mention in this section that the boto package is required.

Role Variables
--------------

	middle_earth_local_dir: "../../../" # Traversing back roles/ansible-middle-relay-middle-earth/tasks
	tor_path: "{{ middle_earth_local_dir }}/tor"
	tor_data_path: "{{ crawler_path }}/{{ tbb_dirname }}/Browser/TorBrowser/Data/"

Dependencies
------------

	- { role: parmegv.ansible-custom-tor, custom_tor_src_dir: "{{ tor_path }}" }
	- { role: parmegv.ansible-onionperf }

Example Playbook
----------------

Including an example of how to use your role (for instance, with variables passed in as parameters) is always nice for users too:

    - hosts: servers
      roles:
         - { role: username.rolename, x: 42 }

License
-------

BSD

Author Information
------------------

An optional section for the role authors to include contact information, or a website (HTML is not allowed).
