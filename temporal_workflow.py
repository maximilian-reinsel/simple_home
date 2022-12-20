# localhost:7233

import asyncio
import logging
from datetime import datetime, timedelta
from temporalio import workflow, activity
from temporalio.client import Client
from temporalio.worker import Worker
from pylutron_caseta.smartbridge import Smartbridge
from typing import Dict, List, Tuple

#[{'device_id': '2', 'current_state': 0, 'fan_speed': None, 'tilt': None, 'zone': '1', 'name': 'Dining Room_Right Window', 'button_groups': None, 'occupancy_sensors': None, 'type': 'SerenaHoneycombShade', 'model': 'CSX-YJ-XX', 'serial': 81733602, 'device_name': 'Right Window', 'area': '2'},
#{'device_id': '3', 'current_state': 0, 'fan_speed': None, 'tilt': None, 'zone': '2', 'name': 'Dining Room_Left Window', 'button_groups': None, 'occupancy_sensors': None, 'type': 'SerenaHoneycombShade', 'model': 'CSX-YJ-XX', 'serial': 91532992, 'device_name': 'Left Window', 'area': '2'},
#{'device_id': '5', 'current_state': 0, 'fan_speed': None, 'tilt': None, 'zone': '3', 'name': 'Master Bedroom_Right Window', 'button_groups': None, 'occupancy_sensors': None, 'type': 'SerenaHoneycombShade', 'model': 'CSX-YJ-XX', 'serial': 81733606, 'device_name': 'Right Window', 'area': '4'},
#{'device_id': '6', 'current_state': 0, 'fan_speed': None, 'tilt': None, 'zone': '4', 'name': 'Master Bedroom_Center Window', 'button_groups': None, 'occupancy_sensors': None, 'type': 'SerenaHoneycombShade', 'model': 'CSX-YJ-XX', 'serial': 91532999, 'device_name': 'Center Window', 'area': '4'},
#{'device_id': '8', 'current_state': 0, 'fan_speed': None, 'tilt': None, 'zone': '6', 'name': 'Master Bedroom_Left Shade', 'button_groups': None, 'occupancy_sensors': None, 'type': 'SerenaHoneycombShade', 'model': 'CSX-YJ-XX', 'serial': 91532980, 'device_name': 'Left Shade', 'area': '4'}]

# await bridge.set_value(device["device_id"], 90) <-- 90% open

async def initialize() -> Smartbridge:
    bridge = Smartbridge.create_tls("192.168.1.190", "/home/maxreinsel/.config/pylutron_caseta/192.168.1.190.key", "/home/maxreinsel/.config/pylutron_caseta/192.168.1.190.crt", "/home/maxreinsel/.config/pylutron_caseta/192.168.1.190-bridge.crt")
    await bridge.connect()
    return bridge

# Assumes shade names are unique.
def get_shades(bridge: Smartbridge, expected: List[str]) -> Dict[str, str]:
    devices = bridge.get_devices_by_domain("cover")
    found_devices = {}
    for d in devices:
        found_devices[d["name"]] = d["device_id"]

    not_found = [e for e in expected if not e in found_devices]
    if not_found:
        logger.warning(f"The following specified devices were not found: {not_found}")

    logger.info(f"Found devices: {found_devices}.")

    return found_devices

async def await_all(task_list):
    logger.info(f"Awaiting {len(task_list)} tasks...")
    for task in tasks:
        await task

    logger.info("Await complete.")

@activity.defn
async def set_shade_levels(device_value_list: List[Tuple[str, int]]) -> None:
    logger = logging.getLogger('set_shade_level')
    logger.info(f"Requested: {device_value_list}.")

    bridge = await initialize()
    found_devices = get_shades(bridge, expected=[name for name,_ in device_value_list])
    
    tasks = [bridge.set_value(found_devices[name], value) for name, value in device_value_list if name in found_devices]
    await_all(tasks)

@activity.defn
async def close_shades(device_list: List[str]) -> None:
    logger = logging.getLogger('close_shades')
    logger.info(f"Requested: {device_list}.")

    bridge = await initialize()
    found_devices = get_shades(bridge, expected=[name for name,_ in device_list])
    
    tasks = [bridge.lower_cover(found_devices[name]) for name in device_value_list if name in found_devices]
    await_all(tasks)

@activity.defn
async def open_shades(device_list: List[str]) -> None:
    logger = logging.getLogger('open_shades')
    logger.info(f"Requested: {device_list}.")

    bridge = await initialize()
    found_devices = get_shades(bridge, expected=[name for name,_ in device_list])
    
    tasks = [bridge.raise_cover(found_devices[name]) for name in device_value_list if name in found_devices]
    await_all(tasks)

@workflow.defn
class MorningDiningRoom:
    @workflow.run
    async def run(self, name: str) -> str:
        return await workflow.execute_activity(
            set_shade_levels, [("Dining Room_Right Window", 66), ("Dining Room_Left Window", 66)], schedule_to_close_timeout=timedelta(seconds=15)
        )

@workflow.defn
class EveningDiningRoomFullUp:
    @workflow.run
    async def run(self, name: str) -> str:
        return await workflow.execute_activity(
            open_shades, ["Dining Room_Right Window", "Dining Room_Left Window"], schedule_to_close_timeout=timedelta(seconds=15)
        )

@workflow.defn
class EveningDiningRoomFullDown:
    @workflow.run
    async def run(self, name: str) -> str:
        return await workflow.execute_activity(
            close_shades, ["Dining Room_Right Window", "Dining Room_Left Window"], schedule_to_close_timeout=timedelta(seconds=15)
        )

async def main():
    # Create client connected to server at the given address
    client = await Client.connect("localhost:7233")

    # Run the worker
    worker = Worker(client, task_queue="shade-controls", workflows=[SayHello], activities=[set_shade_levels, open_shades, close_shades])
    await worker.run()

if __name__ == "__main__":
    asyncio.run(main())