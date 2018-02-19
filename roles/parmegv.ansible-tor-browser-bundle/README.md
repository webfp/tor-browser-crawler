!https://travis-ci.org/parmegv/ansible-tor-browser-bundle.svg?branch=master!:https://travis-ci.org/parmegv/ansible-tor-browser-bundle

Role Name
=========

An Ansible role that installs the Tor Browser Bundle

Requirements
------------

Ansible, this role has been tested with 2.1.1.0.

Role Variables
--------------

	tbb_release: 6.0.6 # Version of the Tor Browser Bundle
	tbb_arch: 64 # Architecture
	tbb_locale: en-US

Example Playbook
----------------

Including an example of how to use your role (for instance, with variables passed in as parameters) is always nice for users too:

    - hosts: servers
      roles:
         - { role: tor-browser-bundle, tbb_release: 6.0.6 }

License
-------

BSD

Author Information
------------------

Rafael Gálvez Vizcaíno
Ph.D. student at ESAT/COSIC KU Leuven
