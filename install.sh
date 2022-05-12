# the default admin user is username:a password: a

apt-get update
apt-get upgrade
apt-get install python3-pip postgresql sqlite3
python3 -m venv ieddit-env
source ieddit-env/bin/activate
pip3 install -r requirements.txt


