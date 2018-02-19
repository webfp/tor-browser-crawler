[![Build Status](https://travis-ci.org/parmegv/ansible-torbutton.svg?branch=master)](https://travis-ci.org/parmegv/ansible-torbutton)
Role Name
=========

An Ansible role to generate and test the Torbutton extension against a given Tor Browser Bundle.

Requirements
------------

This role has been tested with Ansible version 2.2.1.0

Role Variables
--------------

	torbutton_dirpath: "~/"
	torbutton_git_repo_name: "torbutton"

	torbutton_git_repo: "https://git.torproject.org/{{ torbutton_git_repo_name }}.git"
	torbutton_git_tag: "master"

	torbutton_patch: "" # Path to the patch
	torbutton_patched_version: "" # Version of the patched Torbutton, to locate the generated XPI
	torbutton_tor_browser_bundle_path: "" # Path to the Tor Browser Bundle, to move the patched XPI to it

Example Playbook
----------------

    - hosts: servers
      roles:
         - { role: parmegv.ansible-torbutton, torbutton_patch: "~/torbutton_patch", torbutton_patched_version: "1.9.6.1", torbutton_tor_browser_bundle_patch: "~/tor-browser_en-US" }

License
-------

BSD

Author Information
------------------

Rafael Gálvez Vizcaíno
Ph.D. student at ESAT/COSIC KU Leuven
