import re
from collections.abc import Sequence
from io import BytesIO
from typing import TypedDict, cast

from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from django.core.files.uploadedfile import UploadedFile
from pypdf import PdfReader, PdfWriter
from rest_framework import permissions, serializers, status
from rest_framework.parsers import BaseParser, FormParser, JSONParser, MultiPartParser
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from .newprinting_db.admin.admin import is_admin, add_admin, remove_admin
from .newprinting_db.balance.balance_calculator import (
    query_balance,
    safe_withdraw,
    set_balance,
)

# ===========
import os
import uuid
from .newprinting_db.submission.crud import create_submission, mark_submission_refunded
from .newprinting_db.submission.submission import (
    get_jobs_by_username,
    get_job_by_uid,
    get_jobs_by_uid_between,
)
from .newprinting_grpc.scheduler_client import SchedulerClient

# Shared directory for passing files to the Scheduler
SHARED_DIR = os.environ.get("SHARED_PRINT_DIR", "/tmp/shared_printing")
SCHEDULER = SchedulerClient()

# ===========

class PdfUploadData(TypedDict):
    file: serializers.FileField
    duplex: serializers.BooleanField


class PdfUploadSerializer(serializers.Serializer[PdfUploadData]):
    # files = serializers.ListField(child=serializers.FileField(), allow_empty=False)
    files = serializers.ListField(
        child=serializers.FileField(allow_empty_file=False, use_url=False),
        allow_empty=False,
    )
    duplex: serializers.BooleanField = serializers.BooleanField(
        default=False, label="雙面列印"
    )


def ldap_authenticate(username: str, password: str):
    user = authenticate(username=username, password=password)
    return user


def get_user_balance(username: str) -> str:
    return str(query_balance(username))


class LoginView(APIView):
    permission_classes = (permissions.AllowAny,)
    parser_classes: Sequence[type[BaseParser]] = (JSONParser,)

    def post(self, request: Request):
        username: str = str(request.data.get("username"))
        password: str = str(request.data.get("password"))

        user = ldap_authenticate(username, password)
        if user is not None:
            response = Response({"status": "success"}, status=status.HTTP_200_OK)
            login(request, user)
            return response

        return Response(
            {"status": "failed", "errorReason": "Invalid credentials"},
            status=status.HTTP_401_UNAUTHORIZED,
        )


class MeView(APIView):
    def get(self, request: Request):
        if request.user.is_authenticated:
            user: User = cast(User, request.user)
            return Response(
                {
                    "username": user.get_username(),
                    "balance": get_user_balance(user.get_username()),
                }
            )
        else:
            return Response(
                {"message": "Not logged in"}, status=status.HTTP_401_UNAUTHORIZED
            )


class PrintView(APIView):
    parser_classes: Sequence[type[BaseParser]] = (MultiPartParser, FormParser)
    serializer_class: type[PdfUploadSerializer] = PdfUploadSerializer

    def post(self, request: Request):
        serializer = PdfUploadSerializer(data=request.data)

        if not request.user.is_authenticated:
            return Response(
                {"message": "Not logged in"}, status=status.HTTP_403_FORBIDDEN
            )

        if not serializer.is_valid():
            return Response(
                {"message": "Serializer error"}, status=status.HTTP_403_FORBIDDEN
            )

        files: list[UploadedFile] = cast(
            list[UploadedFile], serializer.validated_data["files"]
        )
        duplex: bool = cast(bool, serializer.validated_data["duplex"])
        username = request.user.get_username()

        writer: PdfWriter = PdfWriter()
        price = 0

        # process PDF and calculate price
        for file in files:
            reader: PdfReader = PdfReader(file)

            for page in reader.pages:
                price += 1
                writer.add_page(page)

            if duplex:
                page_count: int = len(reader.pages)
                if page_count % 2 == 1:
                    writer.add_blank_page(page)

        # deduct balance
        if not safe_withdraw(username, price):
            return Response({"message": "Not enough balance"}, status=status.HTTP_402_PAYMENT_REQUIRED)

        # create db skeleton to get uid
        try:
            uid = create_submission(username=username, printer="default", pages=price, money=price)
        except Exception:
            # create submission failed -> refund
            current_balance = query_balance(username)
            set_balance(username, current_balance + price)
            return Response({"message": "Database error during submission"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # atomic file write avoid race condition
        os.makedirs(SHARED_DIR, exist_ok=True)
        temp_filename = f"{uuid.uuid4()}.tmp"
        temp_filepath = os.path.join(SHARED_DIR, temp_filename)
        final_filepath = os.path.join(SHARED_DIR, f"{uid}.pdf")

        try:
            # write to uuid tmp file first
            with open(temp_filepath, "wb") as f:
                writer.write(f)
            
            # atomic rename make sure that scheduler can only access fully written files
            os.rename(temp_filepath, final_filepath)
        except Exception as e:
            # clean up
            if os.path.exists(temp_filepath):
                os.remove(temp_filepath)
            # mark submission as failed / refunded
            current_balance = query_balance(username)
            set_balance(username, current_balance + price)
            mark_submission_refunded(uid, f"File system error: {str(e)}")
            return Response({"message": f"File system error: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # notify scheduler via gRPC
        success = SCHEDULER.submit_job(uid=uid, username=username, total_pages=price)

        if not success:
            # scheduler worker handles pending orphan submissions
            pass

        return Response(
            {
                "jobId": str(uid),
                "balance": get_user_balance(username),
            },
            status=status.HTTP_202_ACCEPTED,
        )

from dataclasses import asdict
class JobListView(APIView):
    def get(self, request: Request):
        if request.user.is_authenticated:
            user: User = cast(User, request.user)
            jobs_list = get_jobs_by_username(user.get_username())
            # jobs_data = [asdict(job) for job in jobs_list]
            jobs_data = [{"jobId": str(job.uid), 'state': job.status} for job in jobs_list]
            return Response(
                {
                    "jobs": jobs_data,
                },
                status=status.HTTP_202_ACCEPTED,
            )
        else:
            return Response(
                {"message": "Not logged in"}, status=status.HTTP_401_UNAUTHORIZED
            )


class JobDetailView(APIView):
    def get(self, request: Request, jobId):
        if not request.user.is_authenticated:
            return Response(
                {"message": "Not logged in"}, status=status.HTTP_401_UNAUTHORIZED
            )

        try:
            uid = int(jobId)
        except (TypeError, ValueError):
            return Response(
                {"message": "Invalid jobId"}, status=status.HTTP_400_BAD_REQUEST
            )

        user: User = cast(User, request.user)
        job = get_job_by_uid(uid)

        if job.uid == -1:
            return Response(
                {"message": "Not Found"}, status=status.HTTP_404_NOT_FOUND
            )

        if job.username != user.get_username() and not is_admin(user.get_username()):
            return Response(
                {"message": "Not Found"}, status=status.HTTP_404_NOT_FOUND
            )

        return Response(
            {
                "username": job.username,
                "pages": job.pages,
                "money": job.money,
                "create_time": job.created_at,
                "status": job.status,
            }
        )

class AdminTransferView(APIView):
    parser_classes: Sequence[type[BaseParser]] = (JSONParser,)

    def post(self, request: Request):
        if not request.user.is_authenticated:
            return Response("Not logged in", status=status.HTTP_401_UNAUTHORIZED)

        current_user: User = cast(User, request.user)

        if not is_admin(current_user.get_username()):
            return Response(
                "Current user is not admin", status=status.HTTP_403_FORBIDDEN
            )

        username: str = str(request.data.get("username"))
        amount: str = str(request.data.get("amount"))
        (result, _message) = set_balance(username, int(amount))
        if result:
            return Response("success", status=status.HTTP_200_OK)
        else:
            return Response("failed", status=status.HTTP_200_OK)


class AdminMeView(APIView):
    def get(self, request: Request):
        if not request.user.is_authenticated:
            return Response(
                {"message": "Not logged in"}, status=status.HTTP_401_UNAUTHORIZED
            )

        current_user: User = cast(User, request.user)
        username = current_user.get_username()
        return Response(
            {"username": username, "is_admin": bool(is_admin(username))},
            status=status.HTTP_200_OK,
        )


class AdminJobsView(APIView):
    def get(self, request: Request):
        if not request.user.is_authenticated:
            return Response(
                {"message": "Not logged in"}, status=status.HTTP_401_UNAUTHORIZED
            )

        current_user: User = cast(User, request.user)
        if not is_admin(current_user.get_username()):
            return Response(
                {"message": "Current user is not admin"},
                status=status.HTTP_403_FORBIDDEN,
            )

        start_raw = request.query_params.get("start")
        end_raw = request.query_params.get("end")
        try:
            start = int(str(start_raw))
            end = int(str(end_raw))
        except (TypeError, ValueError):
            return Response(
                {"message": "Invalid start/end"}, status=status.HTTP_400_BAD_REQUEST
            )

        jobs_list = get_jobs_by_uid_between(start, end)
        jobs_data = [
            {"jobId": str(job.uid), "state": job.status, "username": job.username}
            for job in jobs_list
        ]
        return Response({"jobs": jobs_data}, status=status.HTTP_200_OK)


class AdminUserView(APIView):
    def get(self, request: Request):
        if not request.user.is_authenticated:
            return Response(
                {"message": "Not logged in"}, status=status.HTTP_401_UNAUTHORIZED
            )

        current_user: User = cast(User, request.user)
        if not is_admin(current_user.get_username()):
            return Response(
                {"message": "Current user is not admin"},
                status=status.HTTP_403_FORBIDDEN,
            )

        target_username = request.query_params.get("username")
        if not target_username:
            return Response(
                {"message": "Missing username"}, status=status.HTTP_400_BAD_REQUEST
            )

        jobs_list = get_jobs_by_username(target_username)
        jobs_data = [
            {"jobId": str(job.uid), "state": job.status} for job in jobs_list
        ]

        return Response(
            {
                "username": target_username,
                "balance": get_user_balance(target_username),
                "jobs": jobs_data,
            },
            status=status.HTTP_200_OK,
        )


class AdminJobDetailView(APIView):
    def get(self, request: Request, jobId):
        if not request.user.is_authenticated:
            return Response(
                {"message": "Not logged in"}, status=status.HTTP_401_UNAUTHORIZED
            )

        current_user: User = cast(User, request.user)
        if not is_admin(current_user.get_username()):
            return Response(
                {"message": "Current user is not admin"},
                status=status.HTTP_403_FORBIDDEN,
            )

        try:
            uid = int(jobId)
        except (TypeError, ValueError):
            return Response(
                {"message": "Invalid jobId"}, status=status.HTTP_400_BAD_REQUEST
            )

        job = get_job_by_uid(uid)
        if job.uid == -1:
            return Response(
                {"message": "Job not found"}, status=status.HTTP_404_NOT_FOUND
            )

        return Response(
            {
                "username": job.username,
                "pages": job.pages,
                "money": job.money,
                "create_time": job.created_at,
                "status": job.status,
            }
        )


class AdminAddUserView(APIView):
    parser_classes: Sequence[type[BaseParser]] = (JSONParser,)

    def post(self, request: Request):
        if not request.user.is_authenticated:
            return Response(
                {"message": "Not logged in"}, status=status.HTTP_401_UNAUTHORIZED
            )

        current_user: User = cast(User, request.user)
        if not is_admin(current_user.get_username()):
            return Response(
                {"message": "Current user is not admin"},
                status=status.HTTP_403_FORBIDDEN,
            )

        target_username = str(request.data.get("username"))
        try:
            ok = add_admin(target_username)
        except Exception as e:
            return Response(
                {"status": False, "message": str(e)}, status=status.HTTP_200_OK
            )

        if ok:
            return Response(
                {"status": True, "message": ""}, status=status.HTTP_200_OK
            )
        return Response(
            {"status": False, "message": "add_admin failed"},
            status=status.HTTP_200_OK,
        )


class AdminRemoveUserView(APIView):
    parser_classes: Sequence[type[BaseParser]] = (JSONParser,)

    def post(self, request: Request):
        if not request.user.is_authenticated:
            return Response(
                {"message": "Not logged in"}, status=status.HTTP_401_UNAUTHORIZED
            )

        current_user: User = cast(User, request.user)
        if not is_admin(current_user.get_username()):
            return Response(
                {"message": "Current user is not admin"},
                status=status.HTTP_403_FORBIDDEN,
            )

        target_username = str(request.data.get("username"))
        if target_username == current_user.get_username():
            return Response(
                {"status": False, "message": "Cannot remove yourself"},
                status=status.HTTP_200_OK,
            )

        try:
            ok = remove_admin(target_username)
        except Exception as e:
            return Response(
                {"status": False, "message": str(e)}, status=status.HTTP_200_OK
            )

        if ok:
            return Response(
                {"status": True, "message": ""}, status=status.HTTP_200_OK
            )
        return Response(
            {"status": False, "message": "remove_admin failed"},
            status=status.HTTP_200_OK,
        )
