import asyncio
from automations import get_automations
from temporalio.client import Client
from temporal_workflow import RunShadeAutomation

from async_utils import await_all

async def main():
    automations = get_automations()

    client = await Client.connect("localhost:7233")
    print("CONNECTED")

    results = []

    for automation in automations:
        # Create client connected to server at the given address
        name = automation.name
        cron = automation.schedule.cron_for_start
        print("-----")
        print(automation)
        print("-----")
        print(automation.name)
        print("-----")
        handle = await client.start_workflow(RunShadeAutomation.run, automation, id=automation.name, task_queue="shade-controls", cron_schedule=cron)
        results.append(handle.result())

    print(f"Submitted {len(results)} workflows.")

    await await_all(results)

if __name__ == "__main__":
    asyncio.run(main())