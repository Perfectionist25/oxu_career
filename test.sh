set -o errexit

python3 manage.py check
python3 manage.py collectstatic --noinput
python3 manage.py migrate
