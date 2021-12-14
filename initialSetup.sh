#!/usr/bin/env bash
#reference : https://www.digitalocean.com/community/tutorials/how-to-serve-django-applications-with-uwsgi-and-nginx-on-ubuntu-14-04#install-and-configure-virtualenv-and-virtualenvwrapper
# fix for uwsgi not starting: https://serverfault.com/a/775966
sudo pip3 install virtualenv virtualenvwrapper uwsgi
sudo apt-get install libpq-dev
sudo apt-get install binutils libproj-dev gdal-bin
echo "export VIRTUALENVWRAPPER_PYTHON=/usr/bin/python3" >> ~/.bashrc
echo "export WORKON_HOME=~/Env" >> ~/.bashrc
echo "source /usr/local/bin/virtualenvwrapper.sh" >> ~/.bashrc
source ~/.bashrc
mkvirtualenv sched