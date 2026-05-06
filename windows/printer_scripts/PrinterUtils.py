# uses pywin32
# WARNING, no error handling is done, hence please use try-except methods in the front-end
import sys
import win32print
import os
import subprocess
from dataclasses import dataclass
import datetime

@dataclass
class PrintData:
    printer_name: str
    submit_time: datetime.datetime
    total_pages: int
    job_id: int
    status: str

def wintime_to_systemtime(t):
    return datetime.datetime(
            t.year, t.month, t.day, t.hour, t.minute, t.second
            )
def status_to_str(status_code: int) -> str:
    if status_code & win32print.JOB_STATUS_PRINTING:
        return "printing"
    elif status_code & win32print.JOB_STATUS_PRINTED:
        return "printed"
    elif status_code & win32print.JOB_STATUS_PAPEROUT:
        return "nopaper"
    else:
        return "error"


class Printer:
    def __init__(self, printer_name: str):
        self.SUMATRAPDF_EXE_PATH="SumatraPDF.exe"
        self.printer_name=printer_name
        self.printer_handler = win32print.OpenPrinter(self.printer_name)

    def set_printer_name(self,name: str):
        self.printer_name = name

    def get_printer_command(self, filename: str, is_duplex: bool) -> str:
        base_command = [self.SUMATRAPDF_EXE_PATH, '-print-to', self.printer_name]
        if is_duplex:
            base_command.append('-print-settings')
            base_command.append('duplexlong')
        else:
            base_command.append('-print-settings')
            base_command.append('noduplex')
        base_command.append(filename)
        return base_command

    def get_printer_status(self) -> dict:
        return win32print.GetPrinter(self.printer_handler)

    def raw_job_to_printdata(self, task) -> PrintData:
        return PrintData(printer_name = self.printer_name, submit_time = wintime_to_systemtime(task['Submitted']), total_pages = task['TotalPages'], job_id = task['JobId'], status = status_to_str(task['Status']))
    def get_printer_jobs(self) -> [PrintData]:
        raw_jobs = win32print.EnumJobs(self.printer_handler, 0, -1, 1)
        return [self.raw_job_to_printdata(task) for task in raw_jobs]
    # returns PrintData with job_id = -1 with status being the error message
    def get_printer_job_by_id(self, job_id: int) -> PrintData:
        try:
            raw_job = win32print.GetJob(self.printer_handler, job_id, 1)
            print(raw_job)
            print(type(raw_job))
            return self.raw_job_to_printdata(raw_job)
        except Exception as e:
            return PrintData(job_id = -1, status = f'get_job error with exception {e}', printer_name = self.printer_name, submit_time = datetime.datetime.now(), total_pages = 0)

    def get_latest_job_id(self) -> int:
        jobs = self.get_printer_jobs()
        if len(jobs) == 0:
            return -1
        latest_job = max(jobs, key=lambda j: j.submit_time)
        return latest_job.job_id

    # returns true if job is submitted, DOES NOT MEAN THAT IT IS PRINTED
    # this version DOES NOT check user credicentials, so front-end checks MUST be performed !!!
    def submit_print_job(self, filename: str, is_duplex: bool) -> (bool, int):
        prev_latest_job = self.get_latest_job_id()
        print_command = self.get_printer_command(filename, is_duplex)
        print('entering sumatrapdf')
        subprocess.run(print_command, check=True)
        print('leaving sumatrapdf')
        now_latest_job = self.get_latest_job_id()
        if prev_latest_job == now_latest_job:
            return (False, 0)
        else:
            return (True, now_latest_job)

    def submit_print_job_bytes(self, file_content: bytes, is_duplex: bool) -> (bool, int):
        with open(f"tmp-{self.printer_name}.pdf", 'wb') as f:
            f.write(file_content)
            f.flush()
            return self.submit_print_job(f.name, is_duplex)

import random
def run_get_printer_test():
    ariel1 = Printer("Ariel-1")
    print(ariel1.get_printer_status())
    print(ariel1.get_printer_jobs())
    print(ariel1.get_latest_job_id())
    print(ariel1.get_printer_command("a.txt", False))
    print(ariel1.get_printer_command("a.txt", True))
    input("press enter to test printing")
    import time
    s = time.time()
    print("submitting duplex job...")
    print(ariel1.submit_print_job(r'C:\Users\printw1\Downloads\DSDL.pdf', True))
    print(f"time used: {time.time() - s} seconds")
    # print("submitting no-duplex job...")
    # print(ariel1.submit_print_job(r'C:\Users\printw1\Downloads\DSDL.pdf', False))

def main():
    if len(sys.argv) > 1 and sys.argv[1] == 'getjobs':
        ariel1 = Printer("Ariel-1")
        print(ariel1.get_printer_jobs())
        print(type(ariel1.get_printer_jobs()))
        print(ariel1.get_printer_job_by_id(4))
    elif len(sys.argv) > 1:
        ariel1 = Printer("Ariel-1")
        print(ariel1.submit_print_job(r'C:\Users\printw1\Downloads\DSDL.pdf', False))

    else:
        run_get_printer_test();

if __name__ == "__main__":
    main()
