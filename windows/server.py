import grpc
from concurrent import futures
import time

import scheduler_windows_pb2 as pb2
import scheduler_windows_pb2_grpc as pb2_grpc

# import windows printer utils
from printer_scripts import PrinterUtils

MAX_MESSAGE_LENGTH = 1024 * 1024 * 512 # 512 MB


class PrinterServicer(pb2_grpc.PrinterBridgeServicer):
    
    def ExecutePrintJob(self, request, context):
        print(f"[RECV] Print request for {request.user_id}")
        try:
            print('[server.py] sending print job to PrinterUtils')
            success, job_id = PrinterUtils.submit_print_job_bytes(
                request.file_content, 
                request.is_duplex
            )

            # return to scheduler (job_id cast to string)
            return pb2.PrintResponse(
                success=success,
                message="Windows job submitted",
                job_id=str(job_id) 
            )
        except Exception as e:
            print(f"ExecutePrintJob Error: {e}")
            return pb2.PrintResponse(success=False, message=str(e), job_id="0")

    def GetJobStatus(self, request, context):
        print(f"[QUERY] Job ID: {request.job_id}")
        try:
            # cast to int
            if not request.job_id.isdigit():
                return pb2.StatusResponse(state="Error: Invalid Job ID format")
            target_id = int(request.job_id)
            
            # calls get_printer_job_by_id()
            job_info = PrinterUtils.get_printer_job_by_id(job_id=target_id)
            
            print(f"[DEBUG] Raw Job Data: {job_info}")  # for debug

            # syntax alignment
            return pb2.StatusResponse(
                job_id=str(job_info.job_id),
                total_pages=int(job_info.total_pages),
                submit_time=str(job_info.submit_time),
                state=str(job_info.status)
            )
        except Exception as e:
            print(f"GetJobStatus Error: {e}")
            return pb2.StatusResponse(state=f"Error: {str(e)}")

    def GetAllJobs(self, request, context):
        print("[LIST] Fetching all jobs")
        try:
            # call get_printer_jobs()
            all_jobs = PrinterUtils.get_printer_jobs()
            response = pb2.JobListResponse()
            for job in all_jobs:
                id_str = str(job.job_id) if hasattr(job, 'job_id') else str(job.get('JobId', 'unknown'))
                status_str = str(job.status) if hasattr(job, 'status') else str(job.get('Status', 'unknown'))
                
                response.jobs.append(pb2.StatusResponse(
                    job_id=id_str,
                    state=status_str
                ))
            return response
        except Exception as e:
            print(f"GetAllJobs Error: {e}")
            return pb2.JobListResponse()

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10), options = [
        ('grpc.max_send_message_length', MAX_MESSAGE_LENGTH),
        ('grpc.max_receive_message_length', MAX_MESSAGE_LENGTH)
        ])
    pb2_grpc.add_PrinterBridgeServicer_to_server(PrinterServicer(), server)
    server.add_insecure_port('[::]:50051')
    print("Windows gRPC Server is running on port 50051...")
    server.start()
    server.wait_for_termination()

if __name__ == '__main__':
    serve()
