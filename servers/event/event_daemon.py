#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2013-2014 University of Oslo, Norway
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
"""Event-daemon used for pushing updates to systems"""

import eventconf

import getopt
import processing
import Queue
import thread

import sys
import signal
import ctypes

from Cerebrum import Utils
from Cerebrum.modules.event.NotificationCollector import NotificationCollector
from Cerebrum.modules.event.DelayedNotificationCollector import \
        DelayedNotificationCollector

logger = Utils.Factory.get_logger('cronjob')

def usage(i=0):
    print('usage: python event_daemon.py [--type --no-notifications'
            '--no-delayed-notifications]')
    print('-n --no-notifications            Disable the NotificationCollector')
    print('-d --no-delayed-notifications    '
            'Disable the DelayedNotificationCollector')
    print('')
    print('HUP me ONCE (but not my children) if you want to shut me down'
            'with grace.')
    sys.exit(i)

# TODO: Do I need to pass this?
def log_it(queue, run_state):
    logger.info('Started logging thread')
    # TODO: This is highly incorrect. We should be sure the queue is empty
    # before quitting. Call join or something on the callee in the caller or
    # something
#    run = True
#    while run:
    while run_state.value:
        try:
            entry = queue.get(block=True, timeout=5)
#            empty = False
        except Queue.Empty:
#            empty = True
            continue
        log_func = logger.__getattribute__(entry[0])
        log_func(entry[1])
#        run = not empty or run_state.value
    logger.info('Shutting down logger thread')
    # TODO: Log that it runs, and that it quits?

def signal_hup_handler(signal, frame):
    frame.f_locals['run_state'].value = 0

def main():
    log_queue = processing.Queue()
    # Shared varaiable, used to tell the children to shut down
    run_state = processing.Value(ctypes.c_int, 1)
    # Start the thread that writes to the log
    thread.start_new(log_it, (log_queue, run_state,))

    # Parse args
    try:
        opts, args = getopt.getopt(sys.argv[1:],
                                    't:nd',
                                    ['type=',
                                     'no-notifications',
                                     'no-delayed-notifications'])
    except getopt.GetoptError, err:
        print err
        usage(1)

    conf = None
    notifications = True
    delayed_notifications = True

    for opt, val in opts:
        if opt in ('-t', '--type'):
            conf = eventconf.CONFIG[val]
            # TODO: Verify config here?
        elif opt in ('-n', '--no-notifications'):
            notifications = False
        elif opt in ('-d', '--no-delayed-notifications'):
            delayed_notifications = False

    # Can't run without a config!
    if not conf:
        logger.error('No configuration given')
        run_state.value = 0
        usage(2)

    # We need to store the procecess
    procs = []

    # Import the event handeler we need to use
    # TODO: Make someone do this pretty
    event_handler_class = getattr(Utils.dyn_import(
                                    conf['event_handler_class']), 
                                    conf['event_handler_class'].split('.')[-1])
    
    # The queue of events to be processed
    event_queue = processing.Queue()

    # Create all the event-handeler processes
    for i in range(0, conf['concurrent_workers']):
        procs.append(event_handler_class(conf, event_queue, log_queue,
                                                                    run_state))

    # Create the NotificationCollector if appropriate
    if notifications:
        nc = NotificationCollector(event_queue,
                                   conf['event_channels'],
                                   log_queue,
                                   run_state)
    
    # Create the DelayedNotificationCollector if appropriate
    if delayed_notifications:
        dnc = DelayedNotificationCollector(event_queue,
                                   conf,
                                   log_queue,
                                   run_state)

    # Start all processes
    for x in procs:
        x.daemon = True
        x.start()
   
    # Start the NotificationCollector
    if notifications:
        nc.daemon = True
        nc.start()

    # Start the DelayedNotificationCollector
    if delayed_notifications:
        dnc.daemon = True
        dnc.start()


    # Trap the Hangup-signal, we use this in order to shut down nicely
    signal.signal(signal.SIGHUP, signal_hup_handler)
    signal.pause()
    # TODO: Instead of signal.pause, wait for joinage of proccesses or something

    # TODO: Here
    # - Trap singals. We want to exit cleanly <- Done to some extent.
    #     Verify furter

if __name__ == '__main__':
    main()

