### Creating the SQLite Database, Locally

```python
>>> import sys
>>> sys.path.append(your_app_dr)
>>> from your_app_dir.app import db
>>> db.create_all()
```

#### Add a local login
```python
>>> from your_app_dir.app import User
>>> from werkzeug.security import generate_password_hash
>>> admin = User(username='admin', password_hash=generate_password_hash('pass'))
>>> guest = User(username='guest', password_hash=generate_password_hash('another_pass'))
>>> db.session.add(admin)
>>> db.session.add(guest)
>>> db.session.commit()
```

