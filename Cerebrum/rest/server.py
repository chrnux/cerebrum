# -*- coding: utf-8 -*-

from Cerebrum.rest.api import create_app

app = create_app('restconfig')

if __name__ == '__main__':
    app.run(host=app.config['HOST'],
            port=app.config['PORT'])
