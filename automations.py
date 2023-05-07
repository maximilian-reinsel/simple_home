import yaml
from dataclasses import dataclass
from enum import Enum
from typing import List, Optional, Tuple

class DeviceType(Enum):
    SHADE="SHADE"
    SWITCH="SWITCH"

class SunOffsetType(Enum):
    SUNRISE="SUNRISE"
    SUNSET="SUNSET"

class DeviceStateType(Enum):
    OPEN="OPEN"
    CLOSED="CLOSED"
    ON="ON"
    OFF="OFF"
    AT_VALUE="AT_VALUE"

def _getTypeFromStr(s: str):
    if s.upper() in {"OPEN", "CLOSED", "ON", "OFF", "AT_VALUE"}:
        return s.upper()
    raise ValueError(f"Unknown device state: {s}")

@dataclass
class DeviceState:
    device_state: str
    set_value: Optional[int]


@dataclass
class SunOffset:
    hours: int
    minutes: int
    offset_type: str

@dataclass
class Schedule:
    cron_for_start: str
    sun_offset: Optional[SunOffset]

@dataclass
class Device:
    name: str
    type: str
    tags: List[str]

@dataclass
class DeviceWithState:
    device: Device
    state: DeviceState

@dataclass
class Automation:
    name: str
    device_list: List[DeviceWithState]
    schedule: Schedule

def _get_type(raw_type: str):
    if raw_type.upper() in {"SHADE", "SWITCH"}:
        return raw_type.upper()
    raise ValueError(f"Unknown device type: {raw_type}")

def _get_devices(raw_dictionary: dict) -> dict:
    if not "devices" in raw_dictionary:
        raise ValueError("need devices list")
    raw_devices = raw_dictionary["devices"]
    devices = {}
    for d in raw_devices:
        parsed_type = _get_type(d["type"])
        tags = d["location_tags"] if "location_tags" in d else []
        name = d["name"]
        devices[name] = Device(name=name, type=parsed_type, tags=tags)
    return devices

def _read_schedule(raw_schedule: dict) -> Schedule:
    cron = raw_schedule["cron"]
    if "sunset" in raw_schedule:
        hours = raw_schedule["sunset"]["hours"] if "hours" in raw_schedule["sunset"] else 0
        minutes = raw_schedule["sunset"]["minutes"] if "minutes" in raw_schedule["sunset"] else 0
        return Schedule(cron_for_start=cron, sun_offset=SunOffset(hours=hours, minutes=minutes, offset_type="SUNSET"))
    elif "sunrise" in raw_schedule:
        hours = raw_schedule["sunrise"]["hours"] if "hours" in raw_schedule["sunrise"] else 0
        minutes = raw_schedule["sunrise"]["minutes"] if "minutes" in raw_schedule["sunrise"] else 0
        return Schedule(cron_for_start=cron, sun_offset=SunOffset(hours=hours, minutes=minutes, offset_type="SUNRISE"))
    return Schedule(cron_for_start=cron, sun_offset=None)

def _get_automations(raw_dictionary: dict, devices: dict) -> List[Automation]:
    if not "automations" in raw_dictionary:
        raise ValueError("need automations list")
    raw_automations = raw_dictionary["automations"]
    automations = []

    for raw_automation in raw_automations:
        name = raw_automation["name"]
        raw_devices = raw_automation["devices"]
        devices_with_states = []
        overall_value = None
        if "setting" in raw_automation:
            if type(raw_automation["setting"]) == str:
                overall_value = DeviceState(device_state=_getTypeFromStr(raw_automation["setting"]), set_value=None)
            if type(raw_automation["setting"]) == int:
                overall_value = DeviceState(device_state="AT_VALUE", set_value=raw_automation["setting"])
        if "device_list" in raw_devices:
            explicit_device_list = raw_devices["device_list"]
            for raw_device in raw_devices["device_list"]:
                named_in_list = raw_device["name"]
                state = overall_value if not overall_value is None else DeviceState(device_state="AT_VALUE", set_value=raw_device["value"])
                devices_with_states.append(DeviceWithState(devices[named_in_list], state))
        elif "tags" in raw_devices:
            tags = raw_devices["tags"]
            devices_with_states = [DeviceWithState(device, overall_value) for device in devices.values() if [tag for tag in tags if tag in device.tags]]
        else:
            raise ValueError(f"Raw devices yaml did not contain known configuration. Provided: {raw_devices}")

        raw_schedule = raw_automation["schedule"]
        schedule = _read_schedule(raw_schedule)

        automation = Automation(name=name, device_list=devices_with_states, schedule=schedule)

        automations.append(automation)

    return automations

def get_automations() -> List[Automation]:
    with open("automation_exp.yaml", "r") as f:
        s = f.read()
    raw_dictionary = yaml.safe_load(s)
    devices = _get_devices(raw_dictionary)
    automations = _get_automations(raw_dictionary, devices)
    return automations

if __name__ == "__main__":
    parsed_automations = get_automations()
    for automation in parsed_automations:
        print(automation)
        print("---------")
