# app/__init__.py

import os
from rq import Queue
from redis import Redis
from flask import Flask
from rq_scheduler import Scheduler

from config import app_config
from extensions import bcrypt, cors, mail, db, migrate

app = Flask(__name__, instance_relative_config=True)

env = os.environ.get('FLASK_ENV')

app.config.from_object(f"config.{app_config[env if env in app_config.keys() else 'production']}")

db.init_app(app)
mail.init_app(app)
cors.init_app(app)
bcrypt.init_app(app)
migrate.init_app(app, db)


def create_app():
    global app

    def process_str(string):
        return string and type(string) == str

    from dotenv import dotenv_values, load_dotenv
    flask_config = dotenv_values(".flaskenv")
    flask_env = flask_config.get('FLASK_ENV')

    config_name = flask_env if process_str(flask_env) else 'production'

    load_dotenv('.env')

    if config_name not in app_config.keys():
        config_name = 'development'
    app.config.from_object(".".join(["config", app_config[config_name]]))

    from . import models, utils, routes, views

    # Initialize Redis
    redis_url = utils.Helper.generate_redis_url()
    app.redis = Redis.from_url(redis_url if redis_url and type(redis_url) == str else 'redis://')

    # Queue for tasks to be run ASAP
    app.task_queue = Queue(f'{app.config["REDIS_ROOT"]}_tasks', connection=app.redis)
    # Scheduler for tasks to be run at given periods
    app.scheduler = Scheduler(f'{app.config["REDIS_ROOT"]}_scheduler', connection=app.redis)

    # Instantiate pyOTP for generating OTPs
    import pyotp
    base32secret = app.config.get('OTP_BASE32_SECRET', pyotp.random_base32()) or pyotp.random_base32()
    app.totp = pyotp.TOTP(base32secret, digits=6, interval=1 * 60 * 60)  # Let otp be valid for 1 hour in seconds

    return app


# Executes before the first request is processed.
@app.before_first_request
def init_db():
    """
    Method creates and initializes the models used
    :return: None
    """
    from app import models, utils, controllers

    try:
        # Create any database tables that don't exist yet.
        db.create_all()

        try:
            db.session.commit()
        except Exception as ex:
            utils.system_logging(ex, exception=True)
            db.session.rollback()

        try:
            import json
            import uuid

            with open('database.json') as fp:
                values = json.load(fp)

                for receipt in values.get('receipt'):
                    if not models.ReceiptModel.query.filter_by(
                            created_at=receipt.get('created_at'),
                            description=receipt.get('description'),
                            merchant_id=receipt.get('merchant_id'),
                            status=receipt.get('status'),
                            value=receipt.get('value'),
                    ).all():
                        r = models.ReceiptModel(
                            id=uuid.uuid4(),
                            created_at=receipt.get('created_at'),
                            description=receipt.get('description'),
                            merchant_id=receipt.get('merchant_id'),
                            status=receipt.get('status'),
                            value=receipt.get('value'),
                        )
                        r.save()

                for sale in values.get('sales'):
                    if not models.SaleModel.query.filter_by(
                            chip_id=sale.get('chip_id'),
                            created_at=sale.get('created_at'),
                            description=sale.get('description'),
                            id_sale=sale.get('id_sale'),
                            merchant_id=sale.get('merchant_id'),
                            status=sale.get('status'),
                    ).all():
                        s = models.SaleModel(
                            id=uuid.uuid4(),
                            chip_id=sale.get('chip_id'),
                            created_at=sale.get('created_at'),
                            description=sale.get('description'),
                            id_sale=sale.get('id_sale'),
                            merchant_id=sale.get('merchant_id'),
                            status=sale.get('status'),
                        )
                        s.save()

                for transaction in values.get('transaction'):
                    if not models.TransactionModel.query.filter_by(
                            created_at=transaction.get('created_at'),
                            transaction_id=transaction.get('transaction_id'),
                            merchant_id=transaction.get('merchant_id'),
                            value=transaction.get('value'),
                    ).all():
                        t = models.TransactionModel(
                            id=uuid.uuid4(),
                            created_at=transaction.get('created_at'),
                            transaction_id=transaction.get('transaction_id'),
                            merchant_id=transaction.get('merchant_id'),
                            value=transaction.get('value'),
                        )
                        t.save()
        except Exception as err:
            utils.system_logging(f'Error saving existing financials:\n{err}', exception=True)

        # TODO
        # controllers.TasksController.launch_task(
        #    'handle_unhandled_messages',
        #    "Handle unanswered messages",
        #    meta={'startup': True},  # Data to be set on meta of task
        # )
    except Exception as e:
        # Log any error that occurs
        utils.system_logging(e, exception=True)
