# balance sqlite3 test server
## Notes
It works by inserting those unseen names with an `INITIAL_BALANCE`, therefore it assumes all passed users are already checked and valid!

## API
`def query_balance(username: str) -> int`: 
    - if user doesn't exist, creates a new entry of the user with `INITIAL_BALANCE` money
    - returns -1 if fails to query username(which shouldn't happen), returns the balance of user on success
`def safe_withdraw(username: str, amount: int) -> (bool, str)`:
    - creates a new entry for user with `INITIAL_BALANCE` if user not exist
    - returns True if safely withdrawn
    - returns False and an error message on error
