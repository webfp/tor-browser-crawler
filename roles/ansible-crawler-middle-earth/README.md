Role Name
=========

An Ansible role to deploy a the crawler used in the Middle Earth project

Requirements
------------

This role has been tested with Ansible 2.2.1.0

Role Variables
--------------

The referenced variables come from the dependency roles.

	virtualenv_path: "~/.virtualenvs/crawler"
	crawler_local_src_dir: '../../crawler/'
	tor_path: "{{ crawler_local_src_dir }}/tor"
	crawler_path: "~/tor-browser-crawler"
	tbb_dirname: "tor-browser_en-US"
	website_to_stop: "facebook.com"

	urls_dirpath: "{{ crawler_path }}/etc"
	urls_filename: "localized-urls-100-top.csv"
	tor_data_path: "{{crawler_path }}/{{ tbb_dirname }}/Browser/TorBrowser/Data/"


Dependencies
------------

	- { role: parmegv.ansible-tor-browser-crawler , crawler_virtualenv_path: "{{ virtualenv_path }}" }
	- { role: parmegv.ansible-custom-tor, custom_tor_src_dir: "{{ tor_path }}" }
	- { role: parmegv.ansible-onionperf, onionperf_virtualenv_path: "{{ virtualenv_path }}" }
	- { role: parmegv.ansible-torbutton, torbutton_tor_patch: "{{ tor_path }}/test_url_cell/torbutton.patch", torbutton_patched_version: "1.9.6.1", torbutton_tor_browser_bundle_path: "{{ crawler_path }}/tor-browser_en-US", torbutton_git_repo: "https://git.torproject.org/user/gk/{{ torbutton_git_repo_name }}.git", torbutton_git_tag: "rob" }

Example Playbook
----------------

Including an example of how to use your role (for instance, with variables passed in as parameters) is always nice for users too:

    - hosts: servers
      roles:
         - { role: ansible-crawler-middle-earth }

License
-------

BSD

Author Information
------------------

An optional section for the role authors to include contact information, or a website (HTML is not allowed).
