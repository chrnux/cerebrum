#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2015-2016 University of Oslo, Norway
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
>>> from Cerebrum.modules.event_publisher.config import load_config
>>> from Cerebrum.modules.event_publisher.amqp_publisher import (
...     PublishingAMQP091Client)
>>> c = PublishingAMQP091Client(load_config())
>>> c.publish(['ost', 'fisk'])
>>> c.publish('kolje')
>>> c.close()
"""

import datetime
import json

import pika

from Cerebrum.modules.event.clients import ClientErrors
from Cerebrum.modules.event.clients.amqp_client import BaseAMQP091Client
from . import scim


class PublishingAMQP091Client(BaseAMQP091Client):
    """AMQP 0.9.1 client wrapper usable for publishing messages."""

    def __init__(self, config):
        """Init the Pika AMQP 0.9.1 wrapper client.

        :type config: AMQPClientPublisherConfig
        :param config: The configuration for the AMQP client.
        """
        super(PublishingAMQP091Client, self).__init__(config)
        self.exchange = config.exchange_name
        self.exchange_type = config.exchange_type
        self.exchange_durable = config.exchange_durable

    def open(self):
        super(PublishingAMQP091Client, self).open()
        # Declare exchange
        self.channel.exchange_declare(
            exchange=self.exchange,
            exchange_type=self.exchange_type,
            durable=self.exchange_durable)
        # Ensure that messages are recieved by the broker
        self.channel.confirm_delivery()

    def publish(self, messages, durable=True):
        """Publish a message to the exchange.

        :type messages: dict or list of dicts.
        :param messages: The message(s) to publish.

        :type durable: bool
        :param durable: If this message should be durable.
        """
        if isinstance(messages, (dict, scim.Event)):
            messages = [messages]
        elif not isinstance(messages, list):
            raise TypeError('messages must be a dict, event or a list thereof')
        for message in messages:
            if not isinstance(message, (dict, scim.Event)):
                raise TypeError('messages must be a dict, '
                                'Event or a list thereof')
            try:
                err_msg = 'Could not generate routing key'
                if isinstance(message, dict):
                    if 'routing-key' in message:
                        event_type = message['routing-key']
                    else:
                        event_type = 'unknown'
                    payload = message
                else:
                    event_type = message.key
                    payload = message.get_payload()
                msg_body = dict(filter(lambda x: x[0] != 'routing-key',
                                       payload.items()))
                err_msg = ('Could not generate'
                           ' application/json content from message')
                msg_body = json.dumps(msg_body)
            except Exception as e:
                raise ClientErrors.MessageFormatError('{0}: {1}'.format(
                    err_msg,
                    e))
            try:
                if self.channel.basic_publish(
                        exchange=self.exchange,
                        routing_key=event_type,
                        body=msg_body,
                        properties=pika.BasicProperties(
                            # Delivery mode:
                            # 1: Non-persistent
                            # 2: Persistent
                            delivery_mode=2,
                            content_type='application/json'),
                        # Makes publish return false if
                        # the message is not routed / published
                        mandatory=False,
                        # TODO: Should we enable immediate?
                ):
                    return True
                else:
                    raise Exception('Broker did not confirm message delivery')
            except Exception as e:
                raise ClientErrors.MessagePublishingError(
                    'Unable to publish message: {0!r}'.format(e))


class SchedulingAndPublishingAMQP091Client(PublishingAMQP091Client):
    """
    Client with scheduling (celery) capabilities
    """

    def publish(self, messages, durable=True):
        """
        Publish a message to the exchange after scheduling it
        in case it is marked for scheduling

        :type messages: dict, scim.Event or list of dicts and / or scim.Event
        :param messages: The message(s) to publish

        :type durable: bool
        :param durable: If this message should be durable

        :rtype: dict
        :return: A dict of jti:(celery.result.AsyncResult, eta)
        """
        from Cerebrum.modules.celery_tasks.apps.scheduler import schedule_message
        super(SchedulingAndPublishingAMQP091Client, self).publish(
            messages,
            durable)
        if isinstance(messages, (dict, scim.Event)):
            messages = [messages]
        elif not isinstance(messages, list):
            raise TypeError('messages must be a dict, event or a list thereof')
        result_tickets = dict()
        for message in messages:
            if not isinstance(message, (dict, scim.Event)):
                raise TypeError('messages must be a dict, '
                                'Event or a list thereof')
            try:
                if isinstance(message, dict):
                    err_msg = 'Could not extract schedule time'
                    if 'nbf' not in message:
                        continue
                    eta = datetime.datetime.fromtimestamp(int(message['nbf']))
                    jti = message.get('jti', 'invalid')
                    err_msg = 'Could not get routing-key'
                    routing_key = message.get('routing-key', 'unknown')
                    err_msg = 'Could not produce message-body'
                    body = json.dumps(dict(
                        filter(lambda x: x[0] != 'routing-key',
                               message.items())))
                else:
                    # scim.Event
                    err_msg = 'Could not extract schedule time'
                    if not isinstance(message.scheduled, datetime.datetime):
                        continue
                    eta = message.scheduled
                    jti = message.jti or 'invalid'
                    err_msg = 'Could not get routing-key'
                    routing_key = message.key
                    err_msg = 'Could not produce message-body'
                    body = json.dumps(message.get_payload())
                err_msg = 'Could not schedule / produce task'
                result_tickets[jti] = (schedule_message.apply_async(
                    kwargs={'routing_key': routing_key,
                            'body': body},
                    eta=eta), eta)
            except Exception as e:
                raise ClientErrors.MessageFormatError('{0}: {1}'.format(
                    err_msg,
                    e))
        return result_tickets
