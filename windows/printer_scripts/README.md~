# Some APIs for the front end to use:
```
@dataclass
class PrintData:
    submit_time: datetime.datetime
    total_pages: int
    job_id: int
    status: str

class Printer:
    def __init__(printer_name)
    def get_printer_jobs() -> [PrintData]

    # returns PrintData(job_id = -1, status = error_msg) when fails
    def get_printer_job_by_id(job_id: int) -> PrintData

    # sets the printer name
    def set_printer_name(printer_name: str) -> ()

    # returns true if job is submitted
    def submit_print_job(filename: str, is_duplex: bool) -> (bool, int):

    # does the exactly same as submit_print_job but first writes the bytes
    def submit_print_job_bytes(file_content: bytes, is_duplex: bool) -> (bool, int):
        with open(f"tmp-{self.printer_name}.txt", 'wb') as f:
            f.write(file_content)
            f.flush()
            return submit_print_job(username, decrypted_password, f.name, is_duplex)
```
