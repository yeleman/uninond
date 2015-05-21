# uninond
Système SMS d'alerte rapide pour la DRPC de MOPTI

## Install
Ubuntu 14.04.2 with:
  
* Language: French
* Keyboard: French
* User: uninond
* Add OpenSSH

## Packages to install

	acpi acpid alsa-base alsa-utils feh firefox firefox-locale-fr fluxbox git-core gtk-chtheme gtk2-engines gtk2-engines-murrine hostapd python-pip tango-icon-theme vim xdotool unzip isc-dhcp-server

## Configuration

* Launch firefox once and configure homepage to http://localhost:8000
* configure sound (unmute) via: `sudo alsamixer`
* Deploy configuration (as root)
    `# /home/uninond/uninond/uninond/scripts/deploy_conf.sh`
* Install python-acpi as root
		
		# wget -O python-acpi.zip https://github.com/sika-others/python-acpi/archive/master.zip
        # unzip python-acpi && cd python-acpi && python ./setup.py
* Create virtualenv and start project

        # pip install pew
        $ pew new uninondenv
        $ pip install -r requirements.pip

        $ ./manage.py syncdb
        $ ./manage.py migrate
        $ ./manage.py loaddata uninond/fixtures/Location.xml
* reboot

## Phone configuration

* Configure WiFi:
    * SSID: UNINOND
    * IP: 10.0.0.2
    * gateway: 10.0.0.1
    * netmask: /24 
* Install FondaSMS (0.2 on rooted phone or 0.5 on regular)
* Configure FondaSMS:
    * Server URL: `http://10.0.0.1:8000/fondasms`
    * Phone Number: `96172222`
    * Poll interval: 15 seconds
    * _not_ Keep new message
    * WiFi Sleep Policy: always stay connected
    * Network failover: do nothing
    * Enable fondaSMS
