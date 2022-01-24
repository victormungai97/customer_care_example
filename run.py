# run.py

"""
This module will be the starting point of the server
"""

async_mode = None

if async_mode is None:
    try:
        import eventlet

        async_mode = 'eventlet'
    except ImportError:
        pass

    if async_mode is None:
        try:
            from gevent import monkey

            async_mode = 'gevent'
        except ImportError:
            pass

    if async_mode is None:
        async_mode = 'threading'

# monkey patching is necessary because this application uses a background thread
if async_mode == 'eventlet':
    import eventlet

    eventlet.monkey_patch()
elif async_mode == 'gevent':
    from gevent import monkey

    monkey.patch_all()

from app import create_app

from dotenv import dotenv_values, load_dotenv

flask_config = dotenv_values(".flaskenv")

load_dotenv('.env')

app = create_app()
CONSTANTS = {}


@app.shell_context_processor
def make_shell_context():
    """
    Configures a "shell context", which is a list of other symbols to pre-import in flask shell.
    This helps us to work with Python entities without having to import them.
    When flask shell command runs, it'll invoke this function & register the items returned by it in the shell session.
    The dictionary keys are the names under which the symbols are saved in shell
    """
    from app.communication import app_communication
    from app.controllers import app_controllers
    from app.models import app_models
    from app.views import app_views
    from app.utils import app_utils

    CONSTANTS.update(app_models)
    CONSTANTS.update(app_communication)
    CONSTANTS.update(app_controllers)
    CONSTANTS.update(app_views)
    CONSTANTS.update(app_utils)

    return CONSTANTS


if __name__ == '__main__':
    from app.views import socketIO

    port = flask_config.get('FLASK_RUN_PORT')
    # Run SocketIO server which is robust and incorporates standard Flask development server startup
    socketIO.run(
        app,
        debug=app.debug,
        host=flask_config.get('FLASK_RUN_HOST', 'localhost'),
        port=int(port if port and type(port) == str and port.isnumeric() else 5000),
    )
