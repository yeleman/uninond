# uninond
Système SMS d'alerte rapide pour la DRPC de MOPTI

## Install
Ubuntu 14.04.2 with:
  
* Language: French
* Keyboard: French
* User: uninond
* Add OpenSSH

## Packages to install

	acpi alsa-base alsa-utils feh firefox firefox-locale-fr fluxbox git-core gtk-chtheme gtk2-engines gtk2-engines-murrine hostapd python-pip tango-icon-theme vim xdotool unzip

## Configuration

* Launch firefox once and configure homepage to http://localhost:8000
* configure sound (unmute) via: `sudo alsamixer`
* Deploy configuration (as root)
    `# /home/uninond/uninond/uninond/scripts/deploy_conf.sh`
* Install python-acpi as root
		
		# wget -O python-acpi.zip https://github.com/sika-others/python-acpi/archive/master.zip
        # unzip python-acpi && cd python-acpi && python ./setup.py install
* Create virtualenv and start project

        # pip install pew
        $ pew new uninondenv
        $ wget -O python-acpi.zip https://github.com/sika-others/python-acpi/archive/master.zip
        $ unzip python-acpi && cd python-acpi && python ./setup.py install

        $ git clone https://github.com/yeleman/uninond.git
        $ cd uninond
        $ pip install -r requirements.pip

        $ ./manage.py syncdb
        $ ./manage.py migrate
        $ ./manage.py loaddata uninond/fixtures/Location.xml
* reboot
