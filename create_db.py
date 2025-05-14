from app import create_app, db


def populate_database():
    app = create_app()
    with app.app_context():
        print(f"Initializing database at {app.config['SQLALCHEMY_DATABASE_URI']}...")
        db.drop_all()
        db.create_all()


if __name__ == "__main__":
    populate_database()
