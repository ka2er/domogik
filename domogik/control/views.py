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
# $LastChangedDate: 2008-10-11 17:53:14 +0200 (sam. 11 oct. 2008) $
# $LastChangedRevision: 136 $

from django.shortcuts import render_to_response
from domogik.control.models import Room
from domogik.control.models import Capacity
from domogik.control.models import Item

def index(request):
	pageTitle = "Main page of Domogik"
	return render_to_response('index.html', {'pageTitle': pageTitle})

def rooms(request):
	pageTitle = "List of the rooms"
	roomList = Room.objects.all()
	return render_to_response(
		'rooms.html',
		{
			'pageTitle'	: pageTitle,
			'roomList'	: roomList
		}
	)

def capacities(request, roomId):
	room = Room.objects.get(pk=roomId)
	capacityList = Capacity.objects.filter(room__id=roomId)
	pageTitle = "List of the capacities for : " + room.name
	return render_to_response(
		'capacities.html',
		{
			'pageTitle'		: pageTitle,
			'roomName' 		: room.name,
			'capacityList' 	: capacityList
		}
	)

def items(request, capacityId):
	capacity = Capacity.objects.get(pk=capacityId)
	room = Room.objects.get(capacity__id=capacity.id)
	# itemList = Item.objects.filter(capacity__id=capacityId)
	pageTitle = "List of the items for the capacity  : " + capacity.name + " (" + room.name + ")"
	return render_to_response(
		'items.html',
		{
			'pageTitle': pageTitle,
			'capacityName' : capacity.name
		}
	)

# Views for the admin part

def adminIndex(request):
	pageTitle = "Admin page"
	action = "index"
	return render_to_response(
		'admin_index.html',
		{
			'pageTitle': pageTitle,
			'action': action
		}
	)

def loadSampleData(request):
	__removeAllData()
	# Create sample objects
	temperature = Capacity.objects.create(name="Temperature")
	light = Capacity.objects.create(name="Light")
	music = Capacity.objects.create(name="Music")
	powerPoint = Capacity.objects.create(name="Power point")

	bedroom = Room.objects.create(name="Bedroom")
	bedroom.capacities.add(temperature)
	bedroom.capacities.add(light)
	bedroom.capacities.add(music)
	bedroom.capacities.add(powerPoint)
	lounge = Room.objects.create(name="Lounge")
	lounge.capacities.add(temperature)
	lounge.capacities.add(light)
	lounge.capacities.add(music)
	lounge.capacities.add(powerPoint)
	kitchen = Room.objects.create(name="Kitchen")
	kitchen.capacities.add(temperature)
	kitchen.capacities.add(light)
	kitchen.capacities.add(powerPoint)

	bedroomBedsideLamp = Item.objects.create(name="bedroomBedsideLamp", room=bedroom, capacity=light)
	bedroomLamp = Item.objects.create(name="bedroomLamp", room=bedroom, capacity=light)
	bedroomMusic = Item.objects.create(name="bedroomMusic", room=bedroom, capacity=music)

	loungeLamp = Item.objects.create(name="loungeLamp", room=lounge, capacity=light)
	loungeMusic = Item.objects.create(name="loungeMusic", room=lounge, capacity=music)

	kitchenLamp = Item.objects.create(name="kitchenLamp", room=kitchen, capacity=light)
	kitchenCoffeeMachine = Item.objects.create(name="kitchenCoffeeMachine", room=kitchen, capacity=powerPoint)

	roomList = Room.objects.all()
	capacityList = Capacity.objects.all()
	itemList = Item.objects.all()
	pageTitle = "Load sample data"
	action = "loadSampleData"
	return render_to_response(
		'admin_index.html',
		{
			'pageTitle': pageTitle,
			'action': action,
			'roomList': roomList,
			'capacityList': capacityList,
			'itemList': itemList,
		}
	)

def clearData(request):
	__removeAllData()

	pageTitle = "Remove all data"
	action = "clearData"
	return render_to_response(
		'admin_index.html',
		{
			'pageTitle': pageTitle,
			'action': action
		}
	)

# Remove all objects in the database
def __removeAllData():
	itemList = Item.objects.all()
	for item in itemList:
		item.delete()

	capacityList = Capacity.objects.all()
	for capacity in capacityList:
		capacity.delete()

	roomList = Room.objects.all()
	for room in roomList:
		room.delete()
