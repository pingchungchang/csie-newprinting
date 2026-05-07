from collections.abc import Sequence
from io import BytesIO
from typing import TypedDict, cast

from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from django.core.files.uploadedfile import UploadedFile
from pypdf import PdfReader
from rest_framework import permissions, serializers, status
from rest_framework.parsers import BaseParser, FormParser, JSONParser, MultiPartParser
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from .newprinting_db.balance.balance_calculator import (
    query_balance,
    safe_withdraw,
    set_balance,
)
from .newprinting_grpc.bridge.printer_client import JobResponse, PrinterClient


class PdfUploadData(TypedDict):
    file: serializers.FileField
    duplex: serializers.BooleanField


class PdfUploadSerializer(serializers.Serializer[PdfUploadData]):
    # files = serializers.ListField(child=serializers.FileField(), allow_empty=False)
    file: serializers.FileField = serializers.FileField()
    duplex: serializers.BooleanField = serializers.BooleanField(
        default=False, label="雙面列印"
    )


PRINTER_CLIENT = PrinterClient(target_ip="172.16.127.106", port="50051")


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

        file: UploadedFile = cast(UploadedFile, serializer.validated_data["file"])
        duplex: bool = cast(bool, serializer.validated_data["duplex"])

        foo = file.read()

        bytes_stream = BytesIO(foo)
        reader = PdfReader(bytes_stream)

        # TODO: fill in num_pages
        if safe_withdraw(request.user.get_username(), len(reader.pages)) == False:
            return Response(
                {"message": "Not enough balance"}, status=status.HTTP_200_OK
            )

        response: JobResponse = PRINTER_CLIENT.send_print_job("ta", "ta", foo, duplex)

        print(response)

        if response["job_id"] == "":
            return Response(
                {"jobId": "", "balance": "0.0"}, status=status.HTTP_403_FORBIDDEN
            )

        return Response(
            {
                "jobId": response["job_id"],
                "balance": get_user_balance(request.user.get_username()),
            },
            status=status.HTTP_202_ACCEPTED,
        )


# TODO
class JobListView(APIView):
    def get(self, _request: Request):
        return Response(PRINTER_CLIENT.get_all_jobs(), status=status.HTTP_200_OK)


# TODO
class JobDetailView(APIView):
    def get(self, _request: Request, jobId: str):
        return Response(PRINTER_CLIENT.get_job_status(jobId), status=status.HTTP_200_OK)


class AdminView(APIView):
    def post(self, request: Request):
        username: str = str(request.data.get("username"))
        amount: str = str(request.data.get("amount"))
        (result, message) = set_balance(username, int(amount))
        if result:
            return Response("success", status=status.HTTP_200_OK)
        else:
            return Response("failed", status=status.HTTP_200_OK)
