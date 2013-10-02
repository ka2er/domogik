#!/usr/bin/python
# -*- coding: utf-8 -*-

""" This file is part of B{Domogik} project (U{http://www.domogik.org}).

License
=======

B{Domogik} is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

B{Domogik} is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with Domogik. If not, see U{http://www.gnu.org/licenses}.

Plugin purpose
==============

This plugin manages scenarii, it provides MQ interface

Implements
==========


@author: Maxence Dunnewind
@copyright: (C) 2007-2013 Domogik project
@license: GPL(v3)
@organization: Domogik
"""

import traceback

from domogik.xpl.lib.scenario.manager import ScenarioManager
from domogik.xpl.common.plugin import XplPlugin
from domogik.mq.reqrep.worker import MQRep
from domogik.mq.message import MQMessage


class ScenarioFrontend(XplPlugin):
    """ This class provides an interface to MQ system to allow Scenarii management.
    """

    def __init__(self):
        XplPlugin.__init__(self, name='scenario')
        self._req = MQRep(self._zmq, 'scenario')
        self._backend = ScenarioManager(self.log)
        self.add_stop_cb(self.end)
        self.add_stop_cb(self.shutdown)
        self.log.info("Scenario Frontend and Manager initialized, let's wait for some work.")

    def on_mdp_request(self, msg):
        """ Do real work with message
        msg.get_action() shoult contain XXXX.YYYYYY
        with XXXX in [test, condition, parameter]
        YYYYY in [list, new, etc ...]
        """
        mapping = {'test':
                   {
                   'list': self._backend.list_tests,
                   'new': self._backend.ask_test_instance,
                   },
                   'condition':
                   {
                   'list': self._backend.list_conditions,
                   'new': self._backend.create_condition,
                   'get': self._backend.get_parsed_condition,
                   'evaluate': self._backend.eval_condition
                   },
                   'parameter':
                   {
                   'list': self._backend.list_parameters,
                   },
                   'action':
                   {
                   'list': self._backend.list_actions,
                   'new': self._backend.ask_action_instance
                   }
                }
        try:
            if msg.get_data() == {}:
                payload = mapping[msg.get_action().split('.')[0]][msg.get_action().split('.')[1]]()
            else:
                payload = mapping[msg.get_action().split('.')[0]][msg.get_action().split('.')[1]](**msg.get_data())
            self._mdp_reply(msg.get_action(), "ok", payload)

        except:
            self.log.error("Exception occured during message processing.")
            trace = str(traceback.format_exc())
            self.log.debug(trace)
            self._mdp_reply(msg.get_action(), "error", {"details": trace})

    def _mdp_reply(self, action, status, payload):
        msg = MQMessage()
        msg.set_action(action)
        msg.add_data('status', status)
        msg.add_data('payload', payload)
        self._req.reply(msg.get())

    def end(self):
        """ Shutdown Scenario
        """
        self._backend.shutdown()


if __name__ == "__main__":
    ScenarioFrontend()