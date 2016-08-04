# -*- mode: ruby -*-
# vi: set ft=ruby :

Vagrant.configure(2) do |config|
  config.vm.box = "tknerr/baseimage-ubuntu-14.04"

  config.vm.provider "virtualbox" do |v, override|
    override.vm.box = "debian/jessie64"
  end

  config.vm.synced_folder "./", "/home/vagrant/tor-browser-crawler/", disabled: false
  config.vm.provision "ansible" do |ansible|
    ansible.playbook = "playbook.yml"
  end
end
