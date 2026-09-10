from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import RegisterSerializer, UserSerializer


User = get_user_model()


class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)

        if serializer.is_valid():
            user = serializer.save()

            return Response(
                {
                    "message": "Owner account created successfully.",
                    "user": UserSerializer(user).data,
                },
                status=status.HTTP_201_CREATED,
            )

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST,
        )


class GATCListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.role not in [
            User.Role.LMO,
            User.Role.ADMIN,
        ]:
            return Response(
                {
                    "error": "Only LMO or Admin can view GATCs."
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        users = (
            User.objects
            .filter(
                role=User.Role.GATC,
                is_active=True,
            )
            .order_by("username")
        )

        return Response(
            [
                {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                }
                for user in users
            ]
        )
