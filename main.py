import json
from dataclasses import dataclass
from os import getenv

from devices import TuyaClient, TuyaDeviceLogRequest
from spreadsheet import GspreadClient


@dataclass
class Credentials:
    TUYA_CLIENT_ID: str
    TUYA_SECRET_KEY: str
    GOOGLE_SERVICE_ACCOUNT_CREDENTIALS: dict[str, str]
    DEVICES: list[TuyaDeviceLogRequest]


def load_env():
    creds = Credentials(
        TUYA_CLIENT_ID=getenv("TUYA_CLIENT_ID"),
        TUYA_SECRET_KEY=getenv("TUYA_SECRET_KEY"),
        GOOGLE_SERVICE_ACCOUNT_CREDENTIALS=json.loads(
            getenv("GOOGLE_SERVICE_ACCOUNT_CREDENTIALS")
        ),
        DEVICES=json.loads(getenv("DEVICES")),
    )
    if not all(creds.__dict__.values()):
        raise ValueError("Missing one or more environment variables")
    return creds


def main() -> None:
    credentials = load_env()
    credentials.GOOGLE_SERVICE_ACCOUNT_CREDENTIALS["private_key"] = format(
        credentials.GOOGLE_SERVICE_ACCOUNT_CREDENTIALS["private_key"]
    )
    gspread_client = GspreadClient(
        credentials.GOOGLE_SERVICE_ACCOUNT_CREDENTIALS, "Tuya Device Logs"
    )
    tuya_client = TuyaClient(
        access_id=credentials.TUYA_CLIENT_ID, access_key=credentials.TUYA_SECRET_KEY
    )
    for device in credentials.DEVICES:
        rows = tuya_client.get_device_logs(device)
        last_row_timestamp = gspread_client.get_last_row_timestamp(
            device["device_name"]
        )
        if last_row_timestamp is not None:
            duplicate_index = next(
                (
                    index
                    for (index, row) in enumerate(rows)
                    if row[0] == last_row_timestamp
                ),
                None,
            )
            if duplicate_index is not None:
                rows = rows[duplicate_index + 1 :]
        gspread_client.append_rows(device["device_name"], rows=rows)


if __name__ == "__main__":
    main()
