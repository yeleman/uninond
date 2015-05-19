# uninond
Système SMS d'alerte rapide pour la DRPC de MOPTI

## Install
Ubuntu 14.04.2 with:
  
* Language: French
* Keyboard: French
* User: uninond
* Add OpenSSH

## Packages to install

	acpi alsa-base alsa-utils feh firefox firefox-locale-fr fluxbox git-core gtk-chtheme gtk2-engines gtk2-engines-murrine hostapd python-pip tango-icon-theme vim xdotool 

## Configuration

* Launch firefox once and configure homepage to http://localhost:8000
* configure sound (unmute) via: `sudo alsamixer`
* Deploy configuration (as root)
    `# /home/uninond/uninond/uninond/scripts/deploy_conf.sh`
* Create virtualenv and start project

        # pip install pew
        $ pew new uninondenv
        $ pip install -r requirements.pip

        $ ./manage.py syncdb
        $ ./manage.py migrate
        $ ./manage.py loaddata uninond/fixtures/Location.xml
* reboot
