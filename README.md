### Everything you need to get started
1. Python 3.5 or Higher
2. Pycharm Community Edition
2. Virtual Environment recommended
3. Open an interactive Python console in your project directory

## Before Running Server

### Exporting FLASK_APP Variable
1. FLASK_APP export is needed to run flask commands from shell
1. With venv active and in ```dir ~/mysite```
2. Windows : ```set FLASK_APP=hermes.py```
3. Bash: ```export FLASK_APP=hermes.py```

### Creating the Database, Locally

```
flask run
```

```python
>>> db.create_all()
# SQLAlchemy executes required SQL and the database appears
```

#### Optionally
```bash
flask db init
```

### Add a local login
```python
>>> admin = User(username='admin', user_type='admin', password_hash=generate_password_hash('pass'))
>>> guest = User(username='guest', password_hash=generate_password_hash('another_pass'))
>>> db.session.add(admin)
>>> db.session.add(guest)
>>> db.session.commit()
```
### Starting the server

```flask run```
