# -*- coding: utf-8 -*-

"""
This is the windoor extention to the telldus plugin.
It allows to send sensor.basic message when a window or a door is open or close.
It allows to use a door detector to send xpl dawndusk messages

over the XPL network
Example usage :
 ts = telldusWindoorAPI()
Prototypes :

@author: Sebastien GALLET <sgallet@gmail.com>
@license: GPL(v3)
"""
from domogik.xpl.common.xplconnector import Listener
from domogik.xpl.common.xplmessage import XplMessage
from domogik.xpl.common.plugin import XplPlugin
from domogik.xpl.common.queryconfig import Query

TELLDUS_UNKNOWN=0
TELLDUS_ON=1
TELLDUS_OFF=2

class telldusWindoorAPI:
    '''
    Windoor extension to telldus pugin
    '''
    def __init__(self, plugin):
        '''
        Constructor
        @param plugin : the master plugin.
        '''
        self._plugin = plugin
        self._plugin.log.debug("telldusWindoorAPI.__init__ : Start ...")
        self.devicetype="WINDOOR"
        self._states = {}
        #Create listeners
        self._plugin.log.debug("telldusWindoorAPI.__init__ : Create listeners")
        Listener(self.windoor_cmnd_cb, self._plugin.myxpl,
                 {'schema': 'sensor.request', 'xpltype': 'xpl-cmnd'})
        self._plugin.log.debug("telldusWindoorAPI.__init__ : Done :-)")

    def windoor_cmnd_cb(self, message):
        """
        General callback for all command messages
        @param message : an XplMessage object
        """
        self._plugin.log.debug("telldusWindoorAPI.windoor_cmnd_cb() : Start ...")
        cmd = None
        if 'request' in message.data:
            cmd = message.data['request']
        device = None
        if 'device' in message.data:
            device = message.data['device']
        self._plugin.log.debug("telldusWindoorAPI.windoor_cmnd_cb :  command %s received with device %s" %
                       (cmd,device))
        mess = XplMessage()
        mess.set_type("xpl-stat")
        mess.set_schema("sensor.basic")
        sendit=False
        deviceId=self._plugin.getDeviceId(device)
        if deviceId in self._states.iterkeys():
            state=self._states[deviceId]
        else :
            state=TELLDUS_UNKNOWN
        if cmd=="current":
            mess.add_data({"type" : "windoor"})
            mess.add_data({"device" : device})
            if device!=None:
                if state==TELLDUS_OFF:
                    mess.add_data({"current" :  "LOW"})
                    self._plugin.log.info("telldusWindoorAPI : Send sensor message over XPL with current= %s" % "LOW")
                    sendit=True
                elif state==TELLDUS_ON:
                    mess.add_data({"current" :  "HIGH"})
                    self._plugin.log.info("telldusWindoorAPI : Send sensor message over XPL with current= %s" % "HIGH")
                    sendit=True
                elif state==TELLDUS_UNKNOWN:
                    mess.add_data({"current" :  "UNKNOWN"})
                    self._plugin.log.info("telldusWindoorAPI : Send sensor message over XPL with current= %s" % "UNKNOWM")
                    sendit=True
        if sendit:
            self._plugin.myxpl.send(mess)
        self._plugin.log.debug("telldusWindoorAPI.windoor_cmnd_cb() : Done :)")

    def sendWindoor(self,deviceId,state):
        """
        Send a xPL message of the type SENSOR.BASIC when a door / window is open/close
        @param state : TELLDUS_UNKNOWN | TELLDUS_ON | TELLDUS_OFF
        """
        self._plugin.log.debug("telldusWindoorAPI.sendWindoor() : Start ...")
        self._states[deviceId]=state
        mess = XplMessage()
        mess.set_type("xpl-trig")
        mess.set_schema("sensor.basic")
        mess.add_data({"type" : "windoor"})
        mess.add_data({"device" : self._plugin.getDeviceAddress(deviceId)})
        sendit=False
        if state==TELLDUS_OFF:
            mess.add_data({"current" :  "LOW"})
            self._plugin.log.info("telldusWindoorAPI : Send sensor message over XPL with current= %s" % "LOW")
            sendit=True
        elif state==TELLDUS_ON:
            mess.add_data({"current" :  "HIGH"})
            self._plugin.log.info("telldusWindoorAPI : Send sensor message over XPL with current= %s" % "HIGH")
            sendit=True
        if sendit:
            self._plugin.myxpl.send(mess)
        self._plugin.log.debug("telldusWindoorAPI.sendWindoor() : Done :-)")

if __name__ == "__main__":
    print("TellStick Python binding Class")
    print("Testing mode.\n")
    print("..Creating TellStick object")
    tell = telldusWindoorAPI()
    print("..OK")
    print("..Sending a ON command")
    #tell.sendOn("arctech", "selflearning-switch", "0x12345", "2")
    #tell.sendOn(3)
    print("..OK")
    print("..Sending a OFF command")
    #tell.sendOff("arctech", "selflearning-switch", "0x12345", "3")
    #tell.sendOff(3)
    print("..OK")
    print("\nAll is OK")
