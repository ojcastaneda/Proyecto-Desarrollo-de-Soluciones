apt-get update
apt-get upgrade -y
apt-get install python3-pip python3-venv -y
cd /home/ubuntu
su ubuntu
git clone https://github.com/ojcastaneda/Proyecto-Desarrollo-de-Soluciones.git
cd Proyecto-Desarrollo-de-Soluciones/
python3 -m venv .venv
source .venv/bin/activate
pip install dvc[s3] mlflow
dvc pull --force
cd training/
mlflow server --host 0.0.0.0 --port 5000 --workers 1 --gunicorn-opts "--workers=2"
