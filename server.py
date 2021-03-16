#!/usr/bin/env python

# encoding: utf-8
import json
import os
from datetime import datetime

import rpyc
import asyncio
import json
import time
import keyboard
# Create a RPyC connection to the remote ev3dev device.
# Use the hostname or IP address of the ev3dev device.
# If this fails, verify your IP connectivty via ``ping X.X.X.X``
from azure.eventhub.aio import EventHubConsumerClient
#
robot1 = rpyc.classic.connect('192.168.0.53')

from azure.eventhub.extensions.checkpointstoreblobaio import BlobCheckpointStore

# # robot2 = rpyc.classic.connect('192.168.178.94')
#
# # import ev3dev2 on the remote ev3dev device
# # robot2_motors = robot2.modules['ev3dev2.motor']
# # robot2_sensors = robot2.modules['ev3dev2.sensor']
# # robot2_sensors_lego = robot2.modules['ev3dev2.sensor.lego']
#
robot1_motors = robot1.modules['ev3dev2.motor']
# robot1_sensors = robot1.modules['ev3dev2.sensor']
# robot1_sensors_lego = robot1.modules['ev3dev2.sensor.lego']

addresses = ['outA', 'outB', 'outC', 'outD']
motor_types = ['large', 'medium']
speed = 0
connectionString = 'Endpoint=sb://robot-commands.servicebus.windows.net/;SharedAccessKeyName=RootManageSharedAccessKey;SharedAccessKey=NJOGSGDvFC2/4erXQsULqlT6KYVeB+k6lvJ6uEpllJs='
eventHubName = 'command'
consumerGroup = '$Default'
storageConnectionString = "DefaultEndpointsProtocol=https;AccountName=er1k;AccountKey=HC7zbpwKXoFIrx6xxlwdzdFynTv2Shgx87eqz7I6iYPi/PHzeNHEcdhZ3vrH5guhkFqgBplabGGWwPr/qtXDZg==;EndpointSuffix=core.windows.net"
containerName = "events"


import sys
from datetime import datetime

import rpyc
import asyncio


# # robot2 = rpyc.classic.connect('192.168.178.94')
#
# # import ev3dev2 on the remote ev3dev device
# robot2_motors = robot2.modules['ev3dev2.motor']
# # robot2_sensors = robot2.modules['ev3dev2.sensor']
# # robot2_sensors_lego = robot2.modules['ev3dev2.sensor.lego']
#
import asyncio
import websockets


addresses = ['outA', 'outB', 'outC', 'outD']
motor_types = ['large', 'medium']
speed = 0
tank = robot1_motors.MoveTank('outA', 'outD')
motor = robot1_motors.Motor('outB')

def steer_left():
    global motor
    if motor.position <= 105:
        motor.on_to_position(25, motor.position + 35, 0, 0)


def steer_right():
    global motor
    if motor.position >= -105:
        motor.on_to_position(25, motor.position - 35, 0, 0)



def drive():
    global speed
    if speed > 0:
        speed = 0
    if speed - 10 >= -100:
        speed -= 10
        tank.on(speed, speed)


def reverse():
    global speed
    if speed < 0:
        speed = 0
    if speed + 10 <= 100:
        speed += 10
        tank.on(speed, speed)


def reset():
    global speed
    speed = 0
    tank.off()


def execute_command_safe(func, *args):
    try:
        func(*args)
    except OSError as err:
        print("OS error: {0}".format(err))
    except ValueError:
        print("Could not convert data to an integer.")
    except:
        print("Unexpected error:", sys.exc_info()[0])
        raise


async def on_event(partition_context, event):
    # Print the event data.
    jason_body = event.body_as_json(encoding='UTF-8')

    print(datetime.now())
    #print(event)
    print(jason_body)
    await partition_context.update_checkpoint(event)  # Or update_checkpoint every N events for better performance.
    if not jason_body['command']:
        print('command no recognized')
    elif jason_body['command'] == "LEFT":
        execute_command_safe(steer_left)
    elif jason_body['command'] == "FORWARD":
        execute_command_safe(drive)
    elif jason_body['command'] == "RIGHT":
        execute_command_safe(steer_right)
    elif jason_body['command'] == "REVERSE":
        execute_command_safe(reverse)
    elif jason_body['command'] == "p":
        execute_command_safe(reset)

# def on_command(command):
#     # Print the event data.
#
#     print(datetime.now())
#     #print(event)
#     print(command)
#     print(json.loads(command))
#     command = json.loads(command)
#     if not command['command']:
#         print('command no recognized')
#     elif command['command'] == "LEFT":
#         execute_command_safe(steer_left)
#     elif command['command'] == "FORWARD":
#         execute_command_safe(drive)
#     elif command['command'] == "RIGHT":
#         execute_command_safe(steer_right)
#     elif command['command'] == "REVERSE":
#         execute_command_safe(reverse)
#     elif command['command'] == "p":
#         execute_command_safe(reset)

async def receive(client):
    await client.receive(
        on_event=on_event,
        starting_position="-1",  # "-1" is from the beginning of the partition.
    )

# async def main():
#     uri = "ws://techscape.ae.be"
#     async with websockets.connect(uri, ping_interval=None) as websocket:
#         while True:
#             command = await websocket.recv()
#             on_command(command)

async def main():
    checkpoint_store = BlobCheckpointStore.from_connection_string(storageConnectionString, containerName)
    client = EventHubConsumerClient.from_connection_string(
        connectionString,
        consumerGroup,
        eventhub_name=eventHubName,  # For load balancing and checkpoint. Leave None for no load balancing
        checkpoint_store=checkpoint_store
    )
    async with client:
        await receive(client)


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())