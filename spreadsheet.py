import gspread
from gspread.exceptions import WorksheetNotFound
from gspread.utils import ValueInputOption


class GspreadClient:
    gc: gspread.Client
    spreadsheet: gspread.Spreadsheet

    def __init__(self, credentials: str, spreadsheet_name: str):
        self.gc = gspread.service_account_from_dict(credentials)
        self.spreadsheet = self.gc.open(spreadsheet_name)

    def append_rows(self, worksheet_name: str, rows: list[list[str]]):
        try:
            worksheet = self.spreadsheet.worksheet(worksheet_name)
        except WorksheetNotFound:
            worksheet = self.spreadsheet.add_worksheet(worksheet_name, 1, 1)
        worksheet.append_rows(rows, value_input_option=ValueInputOption.user_entered)

    def get_last_row_timestamp(self, worksheet_name: str):
        try:
            worksheet = self.spreadsheet.worksheet(worksheet_name)
        except WorksheetNotFound:
            return None

        return worksheet.cell(worksheet.row_count, 1).value
