from dataclasses import dataclass
from datetime import datetime
from functools import reduce
from typing import TypedDict

import tinytuya


@dataclass
class TuyaDeviceLogRequest(TypedDict):
    device_name: str
    device_id: str
    codes: list[str]


class TuyaDeviceLog(TypedDict):
    code: str
    event_time: int
    value: str


class TuyaClient:
    device_ids: list[str]

    def __init__(self, access_id: str, access_key: str, api_region: str = "eu"):
        self.client = tinytuya.Cloud(
            apiRegion=api_region, apiKey=access_id, apiSecret=access_key, apiDeviceID=""
        )
        self.device_ids = list(
            map(lambda device: device["id"], self.client.getdevices())
        )

    def get_device_logs(
        self,
        device_request: TuyaDeviceLogRequest,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ):
        if device_request["device_id"] not in self.device_ids:
            raise ValueError(f"Device with id {device_request['device_id']} not found")

        response = self.client.getdevicelog(
            device_request["device_id"],
            start=start_date,
            end=end_date,
            params={"codes": ",".join(device_request["codes"])},
            evtype=7,
        )
        if response["result"]["has_next"]:
            raise NotImplementedError("Pagination not implemented")

        logs: list[TuyaDeviceLog] = response["result"]["logs"]

        def _reduce_function(acc: dict[str, list[TuyaDeviceLog]], log: TuyaDeviceLog):
            if acc.get(str(log["event_time"])) is not None:
                acc[str(log["event_time"])].append(log)
            else:
                acc[str(log["event_time"])] = [log]
            return acc

        groupedby_logs: dict[str, list[TuyaDeviceLog]] = reduce(
            _reduce_function, logs, {}
        )
        rows = []
        for unix_timestamp, logs in groupedby_logs.items():
            ordered_logs = sorted(logs, key=lambda x: x["code"])
            timestamp, _ = divmod(int(unix_timestamp), 1000)
            formatted_date = datetime.fromtimestamp(timestamp).isoformat()
            rows.append(
                [
                    formatted_date,
                    *[ordered_logs["value"] for ordered_logs in ordered_logs],
                ]
            )

        return sorted(rows, key=lambda x: x[0])
