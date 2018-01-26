### Everything you need to get started
1. Python 3.5 or Higher
2. Pycharm Community Edition
2. Virtual Environment recommended
3. Open an interactive Python console in your project directory


### Creating the Database, Locally

```python
>>> import sys
>>> sys.path.append(your_app_dr)
>>> from your_app_dir.app import db
>>> db.create_all()
# SQLAlchemy executes required SQL and the database appears
```

### Add a local login
```python
>>> from your_app_dir.app import User
>>> from werkzeug.security import generate_password_hash
>>> admin = User(username='admin', password_hash=generate_password_hash('pass'))
>>> guest = User(username='guest', password_hash=generate_password_hash('another_pass'))
>>> db.session.add(admin)
>>> db.session.add(guest)
>>> db.session.commit()
```

### Starting the server
1. In PyCharm, run api.py and the server becomes available.
2. The server address is printed to console.
