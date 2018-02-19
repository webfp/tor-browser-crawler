[![Build Status](https://travis-ci.org/parmegv/ansible-swapon.svg?branch=master)](https://travis-ci.org/parmegv/ansible-swapon)

Role Name
=========

An Ansible role that enables a swap device.

Requirements
------------

Ansible, this role has been tested with version 2.1.1.0

Role Variables
--------------

	swap_file: "/swapfile"
	memory_amount: {{ (ansible_memtotal_mb / 1000 / 2)|round(0, 'ceil')|int }}G

Example Playbook
----------------

    - hosts: servers
      roles:
         - { role: ansible-swapon, memory_amount: 1G }

License
-------

BSD

Author Information
------------------

Rafael Gálvez Vizcaíno
Ph.D. student at ESAT/COSIC KU Leuven

