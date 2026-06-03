import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from db import crud

def test_db():
    try:
        # 測試建立一筆 submission
        print("Testing DB insert...")
        job_id = crud.create_submission(uid="123", username="ta1", file_pages=5)
        print(f"Success! Created Job ID: {job_id}")
        
        # 測試撈取 pending
        print("Testing DB fetch...")
        jobs = crud.get_pending_jobs()
        print(f"Fetched {len(jobs)} pending jobs.")
        
    except Exception as e:
        print(f"DB connection failed: {e}")

if __name__ == "__main__":
    test_db()
