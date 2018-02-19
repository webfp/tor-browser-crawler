# -*- mode: ruby -*-
# vi: set ft=ruby :

Vagrant.configure(2) do |config|
  config.vm.box = "tknerr/baseimage-ubuntu-14.04"

  config.vm.provider :docker do |v, override|
    override.vm.box = "tknerr/baseimage-ubuntu-14.04"
    override.ssh.port = 2222
	override.ssh.host = "127.0.0.1"
  end

  config.vm.provider :virtualbox do |v, override|
    override.vm.box = "debian/jessie64"
    config.vm.network "forwarded_port", guest: 2201, host: 2201
    config.vm.network "forwarded_port", guest: 2202, host: 2202
  end

  digital_ocean_config = (JSON.parse(File.read("digital-ocean-machines.json")))
  digital_ocean_config['droplets'].each do |instance|
    droplet_name   = instance[0]
    droplet_value = instance[1]
    config.vm.define droplet_name do |instance|
      instance.vm.provider :digital_ocean do |droplet, override|
        override.vm.box = 'digital_ocean'
        override.vm.box_url = "https://github.com/devopsgroup-io/vagrant-digitalocean/raw/master/box/digital_ocean.box"
        override.ssh.username = digital_ocean_config['ssh_username']
        override.ssh.private_key_path = digital_ocean_config['ssh_private_key_path']
        droplet.token = digital_ocean_config['token']

        override.vm.hostname = droplet_name
        droplet.image = droplet_value['image']
        droplet.region = droplet_value['region']
        droplet.size = droplet_value['ram_size']
      end
    end
  end

  config.vm.synced_folder ".", "/vagrant", disabled: true
  config.vm.synced_folder ".", "/home/vagrant/tor-browser-crawler/", disabled: true
  config.vm.provision "ansible" do |ansible|
    ansible.playbook = "../experiments/basic_crawl.yml"
  end
end
