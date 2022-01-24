# app/utils/misc.py

"""
Contains a wide variety of helper functions
"""


class Helper:

    @classmethod
    def parse_url(cls, url: str) -> str:
        try:
            import re
            from dotenv import dotenv_values
            from urllib.parse import urlparse

            if not cls.detect_url(url):
                return ''
            if dotenv_values(".flaskenv").get('FLASK_ENV') == 'development':
                return f'{urlparse(url).scheme}://{urlparse(url).netloc}/'
            parsed = urlparse(url)
            scheme, netloc = parsed.scheme, parsed.netloc
            return "{}://{}".format(scheme, '.'.join(netloc.split('.')[1:]) if re.search('\.', netloc) else netloc)
        except Exception as ex:
            print(ex)
            return ''

    @staticmethod
    def detect_url(url) -> bool:
        try:
            if not url or type(url) != str:
                return False

            import validators

            result = validators.url(url)

            if isinstance(result, validators.ValidationFailure):
                return False

            return result
        except Exception as ex:
            print(ex)
            return False

    @classmethod
    def validate_url(cls, url, host='Website') -> str or None:
        import requests
        host = host or 'Website'
        try:
            if not cls.detect_url(url):
                return f"{host} URL not valid"

            # make a request to confirm that URL exists and is working
            response = requests.get(url)

            if not response:
                return f"Problem connecting to {host} URL"
            return None
        except requests.ConnectionError:
            return f'{host} URL does not exist on Internet'
        except (Exception,):
            return f"Error validating {host} URL. Contact support"

    @staticmethod
    def generate_redis_url():
        """Get a link pointing to the Redis Server for use in background task queue among other uses"""
        try:
            from dotenv import dotenv_values
            app_config = dotenv_values('.env')
            if dotenv_values(".flaskenv").get('FLASK_ENV') == 'development':
                return app_config.get('REDIS_URL', '')
            else:
                redis_password = app_config.get('REDIS_PASSWORD', None)
                if redis_password:
                    redis_host = app_config.get('REDIS_HOST', 'localhost') or 'localhost'
                    redis_port = int(app_config.get('REDIS_PORT', 6379) or 6379)
                    return f'redis://:{redis_password}@{redis_host}:{redis_port}'
                else:
                    return app_config.get('REDIS_URL', '')
        except Exception as err:
            print(err)
            return 'redis://'
