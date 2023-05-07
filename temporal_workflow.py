# localhost:7233

import asyncio
import logging
import os
import sys
from datetime import datetime, timedelta
from temporalio import workflow, activity
from temporalio.client import Client
from temporalio.worker import Worker
from pylutron_caseta.smartbridge import Smartbridge
from typing import Dict, List, Tuple

from async_utils import await_all
from automations import Automation, DeviceStateType

logger = logging.getLogger('workflow')

async def initialize() -> Smartbridge:
    ip = sys.argv[1]
    config_folder = sys.argv[2]
    bridge = Smartbridge.create_tls(
        ip, 
        os.path.join(config_folder, f"{ip}.key"), 
        os.path.join(config_folder, f"{ip}.crt"),
        os.path.join(config_folder, f"{ip}-bridge.crt"))
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

@activity.defn
async def set_shade_levels(device_value_list: List[Tuple[str, int]]) -> None:
    logger = logging.getLogger('set_shade_level')
    logger.info(f"Requested: {device_value_list}.")
    for name, value in device_value_list:
        print(f"SET TO {name} TO {value}! It is: {datetime.utcnow()}.")
    bridge = await initialize()
    found_devices = get_shades(bridge, expected=[name for name,_ in device_value_list])
    
    tasks = [bridge.set_value(found_devices[name], value) for name, value in device_value_list if name in found_devices]
    await await_all(tasks)
    await bridge.close()

@activity.defn
async def close_shades(device_list: List[str]) -> None:
    logger = logging.getLogger('close_shades')
    logger.info(f"Requested: {device_list}.")

    for name in device_list:
        print(f"CLOSED {name}!  It is: {datetime.utcnow()}.")

    bridge = await initialize()
    found_devices = get_shades(bridge, expected=[name for name in device_list])
    
    tasks = [bridge.lower_cover(found_devices[name]) for name in device_list if name in found_devices]
    await await_all(tasks)
    await bridge.close()

@activity.defn
async def open_shades(device_list: List[str]) -> None:
    logger = logging.getLogger('open_shades')
    logger.info(f"Requested: {device_list}.")

    for name in device_list:
        print(f"OPENED {name}!  It is: {datetime.utcnow()}.")

    bridge = await initialize()
    found_devices = get_shades(bridge, expected=[name for name in device_list])
    
    tasks = [bridge.raise_cover(found_devices[name]) for name in device_list if name in found_devices]
    await await_all(tasks)
    await bridge.close()

@workflow.defn
class SetShadeLevel:
    @workflow.run
    async def run(self, device_value_list: List[Tuple[str, int]]) -> str:
        return await workflow.execute_activity(
            set_shade_levels, device_value_list, schedule_to_close_timeout=timedelta(hours=25)
        )

@workflow.defn
class OpenShades:
    @workflow.run
    async def run(self, device_names: str) -> str:
        return await workflow.execute_activity(
            open_shades, device_names, schedule_to_close_timeout=timedelta(hours=25)
        )

@workflow.defn
class CloseShades:
    @workflow.run
    async def run(self, device_names: str) -> str:
        return await workflow.execute_activity(
            close_shades, device_names, schedule_to_close_timeout=timedelta(hours=25)
        )

@workflow.defn
class RunShadeAutomation:
    @workflow.run
    async def run(self, automation: Automation) -> str:
        close_device_names = [device_and_state.device.name for device_and_state in automation.device_list if device_and_state.state.device_state == "CLOSED"]
        open_device_names = [device_and_state.device.name for device_and_state in automation.device_list if device_and_state.state.device_state == "OPEN"]
        device_value_list = [(device_and_state.device.name, device_and_state.state.set_value) for device_and_state in automation.device_list if device_and_state.state.device_state == "AT_VALUE"]

        await_list = []
        
        await_list.append(workflow.execute_activity(
            close_shades, close_device_names, schedule_to_close_timeout=timedelta(hours=25)
        ))
        await_list.append(workflow.execute_activity(
            open_shades, open_device_names, schedule_to_close_timeout=timedelta(hours=25)
        ))
        await_list.append(workflow.execute_activity(
            set_shade_levels, device_value_list, schedule_to_close_timeout=timedelta(hours=25)
        ))

        await await_all(await_list)

async def main():
    print("Worker started with args: ", sys.argv)
    # Create client connected to server at the given address
    client = await Client.connect("localhost:7233")

    # Run the worker
    worker = Worker(
        client,
        task_queue="shade-controls",
        workflows=[RunShadeAutomation], 
        activities=[set_shade_levels, open_shades, close_shades],
        max_cached_workflows=10,
        max_concurrent_workflow_tasks=10,
        max_concurrent_activities=10)
    await worker.run()

if __name__ == "__main__":
    asyncio.run(main())