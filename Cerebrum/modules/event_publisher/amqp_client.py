#! /usr/bin/env python
# encoding: utf-8
#
# Copyright 2015 University of Oslo, Norway
#
# This file is part of Cerebrum.
#
# Cerebrum is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# Cerebrum is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Cerebrum; if not, write to the Free Software Foundation,
# Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

""" Wrapper of the pika AMQP 0.9.1 client.

# Connect and publish messages with the client:
>>> import amqp_client
>>> c = amqp_client.AMQP091Client({'host': 'tcp://127.0.0.1:6161',
...                               'exchange': '/queue/test',
...                               'transaction': True})
>>> c.publish(['ost', 'fisk'])
>>> c.publish('kolje')
>>> c.commit()
"""

import json

import pika

# from Cerebrum.modules.event_publisher import ClientErrors


class AMQP091Client(object):
    def __init__(self, config):
        """Init the Pika AMQP 0.9.1 wrapper client.

        :type config: dict
        :param config: The configuration for the AMQP client.
            I.e. {'host': 'tcp://127.0.0.1',
                  'exchange-name': 'min_exchange',
                  'exchange-type': 'topic'}
        """
        self.config = config
        self.exchange = self.config.get('exchange-name')
        # TODO: Instantiate pika.credentials.Credentials
        # TODO: Handle TLS
        self.connection = pika.BlockingConnection(
            pika.ConnectionParameters(
                host=self.config.get('hostname'),
                port=int(self.config.get('port')),
                virtual_host=self.config.get('virtual-host')))
        self.channel = self.connection.channel()
        self.channel.exchange_declare(
            exchange=self.exchange,
            exchange_type=self.config.get('exchange-type'))
        self.transactions_enabled = self.config.get('transactions-enabled')
        self.transaction = None

    def publish(self, messages, omit_transaction=False, durable=True):
        """Publish a message to the exchange.

        :type message: string or list of strings.
        :param message: The message(s) to publish.

        :type omit_transaction: bool
        :param omit_transaction: Set to True if you would like to publish a
            message outside a transaction.

        :type durable: bool
        :param durable: If this message should be durable.
        """
        if isinstance(messages, (basestring, dict)):
            messages = [messages]
        for msg in messages:
            event_type = (
                '%s:%s' % (msg.get('category'), msg.get('change')) if
                msg.get('change', None) else msg.get('category'))
            # TODO Should message persistence be configurable?
            # TODO: Should we handle exceptions?
            if self.channel.basic_publish(exchange=self.exchange,
                                          routing_key=event_type,
                                          body=json.dumps(msg),
                                          properties=pika.BasicProperties(
                                              # Make message persistent
                                              # TODO: Is this the correct var?
                                              delivery_mode=2,
                                              content_type='application/json'),
                                          # Makes publish return false if
                                          # message not published
                                          mandatory=True):
                return True
            else:
                # TODO: Should we rather raise an exception?
                return False

    def __del__(self):
        self.connection.close()

    def close(self):
        """Close the connection."""
        self.connection.close()

    def commit(self):
        """Commit the current transaction."""
        if self.transaction:
            raise NotImplementedError()

    def rollback(self):
        """Roll back (ABORT) the current transaction."""
        if self.transaction:
            raise NotImplementedError()
