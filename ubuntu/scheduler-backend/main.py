import logging
import sys
from core.engine import SchedulerEngine
from rpc import server

# debug log format
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    stream=sys.stdout
)

if __name__ == '__main__':
    # 1. run worker as engine
    engine = SchedulerEngine()
    engine.start()

    # 2. run gRPC server with worker reference
    try:
        server.serve(engine, port="50052")
    except KeyboardInterrupt:
        logging.info("Shutting down Scheduler...")
        engine.running = False
