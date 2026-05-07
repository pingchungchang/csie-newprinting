# admin postgresql test server
## API
`def add_admin(username: str) -> bool`: 
    returns True if successfully added (even when dup add)
`def remove_admin(username: str) -> bool`: 
    returns True if successfully removed (even when not exist)
`def is_admin(username: str) -> bool`: 
    returns True if is admin
