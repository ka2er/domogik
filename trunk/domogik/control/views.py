#!/usr/bin/python
#-*- encoding:utf-8 *-*

# Copyright 2008 Domogik project

# This file is part of Domogik.
# Domogik is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# Domogik is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with Domogik.  If not, see <http://www.gnu.org/licenses/>.

# Author : Marc Schneider <marc@domogik.org>

# $LastChangedBy: mschneider $
# $LastChangedDate: 2009-02-22 11:46:25 +0100 (dim. 22 févr. 2009) $
# $LastChangedRevision: 392 $

import datetime
import math
import os
from subprocess import *

from django.db.models import Q
from django.http import Http404
from django.http import QueryDict
from django.shortcuts import render_to_response

from domogik.control.models import Area
from domogik.control.models import Room
from domogik.control.models import DeviceCategory
from domogik.control.models import DeviceProperty
from domogik.control.models import DeviceCmdLog
from domogik.control.models import Device
from domogik.control.models import StateReading
from domogik.control.models import ApplicationSetting
from domogik.control.forms import ApplicationSettingForm

from domogik.control.SampleDataHelper import SampleDataHelper
from domogik.control.XPLHelper import XPLHelper


def index(request):
    """
    Main page
    """
    adminMode = ""
    pageTitle = "Control overview"

    appSetting = __readApplicationSetting()

    qListArea = Q()
    qListRoom = Q()
    qListDeviceCategory = Q()
    if request.method == 'POST': # An action was submitted
        cmd = QueryDict.get(request.POST, "cmd", "")
        if cmd == "filter":
            for area in QueryDict.getlist(request.POST, "area"):
                qListArea = qListArea | Q(room__area__id = area)
            for room in QueryDict.getlist(request.POST, "room"):
                qListRoom = qListRoom | Q(room__id = room)
            for deviceCategory in QueryDict.getlist(request.POST,
                    "deviceCategory"):
                qListDeviceCategory = qListDeviceCategory | Q(category__id=
                    deviceCategory)
        elif cmd == "updateValues":
            __updateDeviceValues(request, appSetting)

    # select_related() should avoid one extra db query per property
    deviceList = Device.objects.filter(qListArea).filter(qListRoom).filter(
            qListDeviceCategory).select_related()

    areaList = Area.objects.all()
    roomList = Room.objects.all()
    deviceCategoryList = DeviceCategory.objects.all()
    techList = Device.TECHNOLOGY_CHOICES

    if appSetting.adminMode == True:
        adminMode = "True"

    return render_to_response('index.html', {
        'areaList': areaList,
        'roomList': roomList,
        'deviceCategoryList': deviceCategoryList,
        'deviceList': deviceList,
        'techList': techList,
        'adminMode': adminMode,
        'pageTitle': pageTitle,
    })


def __updateDeviceValues(request, appSetting):
    """
    Update device values (main control page)
    """
    for deviceId in QueryDict.getlist(request.POST, "deviceId"):
        keyList = QueryDict.getlist(request.POST, "key" + deviceId)
        valueList = QueryDict.getlist(request.POST, "value" + deviceId)
        for i in range(len(keyList)):
            __sendValueToDevice(deviceId, keyList[i], valueList[i], appSetting)

    # Get all values posted over the form
    # For each device :
    #       Check if value was changed
    #       If yes, try to send new value to the device
    #       Log the result


def __sendValueToDevice(deviceId, propertyKey, propertyValue, appSetting):
    """
    Send a value to a device
    """
    error = ""
    # Read previous value, and update it if necessary
    device = Device.objects.get(pk=deviceId)
    deviceProperty = DeviceProperty.objects.get(device__id=deviceId,
            key=propertyKey)
    oldValue = deviceProperty.value
    newValue = propertyValue
    if oldValue != newValue:
        if device.technology.lower() == 'x10':
            error = __sendX10Cmd(device, oldValue, newValue,
                    appSetting.simulationMode)

        if error == "":
            deviceProperty.value = newValue
            if device.isLamp():
                if newValue == "on":
                    deviceProperty.value = 100
                elif newValue == "off":
                    deviceProperty.value = 0

            deviceProperty.save()
            __writeDeviceCmdLog(deviceId, deviceProperty.value,
                    "Nothing special", True)


def __sendX10Cmd(device, oldValue, newValue, simulationMode):
    """
    Send x10 cmd
    """
    output = ""
    xPLSchema = "x10.basic"
    xPLParam = ""
    if device.isAppliance():
        xPLParam = "device="+device.address+","+"command="+newValue
    elif device.isLamp():
        if newValue == "on" or newValue == "off":
            xPLParam = "device="+device.address+","+"command="+newValue
        else:
            # TODO check if type is int and 0 <= value <= 100
            if int(newValue)-int(oldValue) > 0:
                cmd = "bright"
            else:
                cmd = "dim"
            level = abs(int(newValue)-int(oldValue))
            xPLParam = "command=" + cmd + "," + "device=" + device.address + \
                    "," + "level=" + str(level)

    print "**** xPLParam = %s" %xPLParam
    if not simulationMode:
        output = XPLHelper().send(xPLSchema, xPLParam)
    return output


def __writeDeviceCmdLog(deviceId, newValue, newComment, newIsSuccessful):
    """
    Write device command log
    """
    newDevice = Device.objects.get(id=deviceId)
    deviceCmdLog = DeviceCmdLog(
        date = datetime.datetime.now(),
        device = newDevice,
        value = newValue,
        comment = newComment,
        isSuccessful = newIsSuccessful)
    deviceCmdLog.save()


def device(request, deviceId):
    """
    Details of a device
    """
    hasCmdLogs = ""
    adminMode = ""
    pageTitle = "Device details"

    if request.method == 'POST': # An action was submitted
        # TODO check the value of the button (reset or update value)
        __updateDeviceValues(request)

    appSetting = __readApplicationSetting()
    if appSetting.adminMode == True:
        adminMode = "True"

    # Read device information
    try:
        device = Device.objects.get(pk=deviceId)
    except Device.DoesNotExist:
        raise Http404

    if DeviceCmdLog.objects.filter(device__id=device.id).count() > 0:
        hasCmdLogs = "True"

    return render_to_response('device.html', {
        'device': device,
        'hasCmdLogs': hasCmdLogs,
        'adminMode': adminMode,
        'pageTitle': pageTitle,
    })


def deviceCmdLogs(request, deviceId):
    """
    View for logs of a device or all devices
    """
    deviceAll = ""
    pageTitle = "Device logs"
    adminMode = ""

    appSetting = __readApplicationSetting()
    if appSetting.adminMode == True:
        adminMode = "True"

    cmd = QueryDict.get(request.POST, "cmd", "")
    if cmd == "clearLogs" and appSetting.adminMode:
        __clearDeviceCmdLogs(request, deviceId, appSetting.adminMode)

    # Read device logs
    if deviceId == "0": # For all devices
        deviceAll = "True"
        deviceCmdLogList = DeviceCmdLog.objects.all()
    else:
        try:
            deviceCmdLogList = DeviceCmdLog.objects.filter(device__id=deviceId)
        except DeviceCmdLog.DoesNotExist:
            raise Http404

    return render_to_response('device_cmd_logs.html', {
        'deviceId': deviceId,
        'adminMode': adminMode,
        'deviceCmdLogList': deviceCmdLogList,
        'deviceAll': deviceAll,
        'pageTitle': pageTitle,
    })


def __clearDeviceCmdLogs(request, deviceId, isAdminMode):
    """
    Clear logs of a device or all devices
    """
    if deviceId == "0": # For all devices
        DeviceCmdLog.objects.all().delete()
    else:
        try:
            DeviceCmdLog.objects.filter(device__id=deviceId).delete()
        except DeviceCmdLog.DoesNotExist:
            raise Http404


# Views for the admin part


def adminIndex(request):
    """
    Main page of the admin part
    """
    pageTitle = "Admin page"
    action = "index"

    appSettingForm = ApplicationSettingForm(
            instance=__readApplicationSetting())
    return render_to_response('admin_index.html', {
        'appSettingForm': appSettingForm,
        'pageTitle': pageTitle,
        'action': action,
    })


def saveSettings(request):
    if request.method == 'POST':
        # Update existing applicationSetting instance with POST values
        form = ApplicationSettingForm(request.POST,
                instance=__readApplicationSetting())
        if form.is_valid():
            form.save()

    return adminIndex(request)


def loadSampleData(request):
    pageTitle = "Load sample data"
    action = "loadSampleData"

    appSetting = __readApplicationSetting()
    if appSetting.simulationMode != True:
        errorMsg = "The application is not running in simulation mode : "\
                "can't load sample data"
        return render_to_response('admin_index.html', {
            'pageTitle': pageTitle,
            'action': action,
            'errorMsg': errorMsg,
        })

    sampleDataHelper = SampleDataHelper()
    sampleDataHelper.create()

    areaList = Area.objects.all()
    roomList = Room.objects.all()
    deviceCategoryList = DeviceCategory.objects.all()
    deviceList = Device.objects.all()
    techList = Device.TECHNOLOGY_CHOICES

    return render_to_response('admin_index.html', {
        'pageTitle': pageTitle,
        'action': action,
        'areaList': areaList,
        'roomList': roomList,
        'deviceCategoryList': deviceCategoryList,
        'deviceList': deviceList,
        'techList': techList,
    })


def clearData(request):
    pageTitle = "Remove all data"
    action = "clearData"

    appSetting = __readApplicationSetting()
    if appSetting.simulationMode != True:
        errorMsg = "The application is not running in simulation mode : "\
                "can't clear data"
        return render_to_response('admin_index.html', {
            'pageTitle': pageTitle,
            'action': action,
            'errorMsg': errorMsg,
        })

    sampleDataHelper = SampleDataHelper()
    sampleDataHelper.remove()

    return render_to_response('admin_index.html', {
        'pageTitle': pageTitle,
        'action': action,
    })


### Private methods


def __readApplicationSetting():
    if ApplicationSetting.objects.all().count() == 1:
        return ApplicationSetting.objects.all()[0]
    else:
        return ApplicationSetting()
