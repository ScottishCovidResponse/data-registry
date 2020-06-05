find . -path '*/migrations/*.py*' -not -name '__init__.py' -delete
rm db.sqlite3
python3 manage.py makemigrations custom_user
python3 manage.py makemigrations data_management
python3 manage.py migrate
python3 manage.py graph_models data_management -X "BaseModel,DataObject,DataObjectVersion" -E -o schema.dot
dot schema.dot -Tsvg -o static/images/schema.svg
dot schema.dot -Tpng -o static/images/schema.png
python3 manage.py createsuperuser --email admin@example.com --username admin
