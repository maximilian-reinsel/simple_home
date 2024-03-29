import asyncio

from pylutron_caseta.smartbridge import Smartbridge

# Script for testing connections.
async def example():
    bridge = Smartbridge.create_tls("192.168.1.190", "<ip>.key", "<ip>.crt", "<ip>-bridge.crt")
    await bridge.connect()
    device = bridge.get_devices_by_domain("cover")[0]
    print("turning on device")
    await bridge.lower_cover(device["device_id"])
    print("turned on device")
    await bridge.close()
loop = asyncio.get_event_loop()
loop.run_until_complete(example())