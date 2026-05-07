# admin postgresql test server
## Dataclass
```py
@dataclass
class JobData:
    uid: int
    wid: int
    username: str
    printer: str
    created_at: datetime.datetime
    pages: int
    status: str
```
## API
`def create_new_job(data: JobData) -> int`: 
    returns the uid of the newly created job
    returns -1 if failed
`def modify_by_uid(uid: int, entry_name: str, new_value) -> bool`:
    modifies a certain entry of a uid to the new value
        (e.g. `modify_by_uid(4, wid, 40)`
    return True on success
`def get_job_by_uid(uid: int) -> JobData`:
    returns the JobData for the uid
