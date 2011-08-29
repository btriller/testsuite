#!/usr/bin/env python
'''
Copyright (C) 2010, Digium, Inc.
Paul Belanger <pabelanger@digium.com>

This program is free software, distributed under the terms of
the GNU General Public License Version 2.
'''

import sys
import logging, logging.config
import logging.config
import os
from twisted.internet import reactor
from starpy import manager, fastagi

from asterisk import Asterisk

logger = logging.getLogger(__name__)

class TestCase(object):
    ast = []
    ami = []
    fastagi = []
    reactor_timeout = 30
    passed = False
    defaultLogLevel = "WARN"
    defaultLogFileName = "logger.conf"

    def __init__(self):
        self.test_name = os.path.dirname(sys.argv[0])
        self.base = self.test_name.lstrip("tests/")

        self.testStateController = None

        """ Set up logging """
        logConfigFile = os.path.join(os.getcwd(), "%s" % (self.defaultLogFileName))
        if os.path.exists(logConfigFile):
            logging.config.fileConfig(logConfigFile, None, False)
        else:
            print "WARNING: no logging.conf file found; using default configuration"
            logging.basicConfig(level=self.defaultLogLevel)

        logger.info("Executing " + self.test_name)
        reactor.callWhenRunning(self.run)

    def create_asterisk(self, count=1):
        """

        Keywork arguments:
        count --

        """
        for c in range(count):
            logger.info("Creating Asterisk instance %d" % (c + 1))
            self.ast.append(Asterisk(base=self.base))
            # Copy shared config files
            self.ast[c].install_configs("%s/configs" %
                    (self.test_name))
            # Copy test specific config files
            self.ast[c].install_configs("%s/configs/ast%d" %
                    (self.test_name, c + 1))

    def create_ami_factory(self, count=1, username="user", secret="mysecret", port=5038):
        """

        Keywork arguments:
        count --
        username --
        secret --
        port --

        """
        for c in range(count):
            host = "127.0.0.%d" % (c + 1)
            self.ami.append(None)
            logger.info("Creating AMIFactory %d" % (c + 1))
            self.ami_factory = manager.AMIFactory(username, secret, c)
            self.ami_factory.login(host).addCallbacks(self.ami_connect,
                    self.ami_login_error)

    def create_fastagi_factory(self, count=1):

        for c in range(count):
            host = "127.0.0.%d" % (c + 1)
            self.fastagi.append(None)
            logger.info("Creating FastAGI Factory %d" % (c + 1))
            self.fastagi_factory = fastagi.FastAGIFactory(self.fastagi_connect)
            reactor.listenTCP(4573, self.fastagi_factory,
                    self.reactor_timeout, host)

    def start_asterisk(self):
        """

        """
        for index, item in enumerate(self.ast):
            logger.info("Starting Asterisk instance %d" % (index + 1))
            self.ast[index].start()

    def stop_asterisk(self):
        """

        """
        for index, item in enumerate(self.ast):
            logger.info("Stopping Asterisk instance %d" % (index + 1))
            self.ast[index].stop()

    def stop_reactor(self):
        """

        """
        logger.info("Stopping Reactor")
        if reactor.running:
            reactor.stop()

    def run(self):
        """

        """
        reactor.callLater(self.reactor_timeout, self.stop_reactor)

    def ami_login_error(self, ami):
        logger.error("Error logging into AMI")
        self.stop_reactor()

    def ami_connect(self, ami):
        logger.info("AMI Connect instance %s" % (ami.id + 1))
        self.ami[ami.id] = ami

