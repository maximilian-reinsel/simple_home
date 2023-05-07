import asyncio
import logging 

logger = logging.getLogger('await_all')

async def await_all(task_list):
    logger.info(f"Awaiting {len(task_list)} tasks...")
    for task in task_list:
        await task

    logger.info("Await complete.")