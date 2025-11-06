from rest_framework.decorators import api_view
from rest_framework.response import Response
from users.models import CustomUser
from core.models import Branch  # ✅ Make sure this import is added

@api_view(['POST'])
def register_user(request):
    username = request.data.get('username')
    password = request.data.get('password')
    role = request.data.get('role')
    branch_id = request.data.get('branch')

    if CustomUser.objects.filter(username=username).exists():
        return Response({'error': 'Username already exists'}, status=400)

    try:
        branch = Branch.objects.get(id=branch_id)  # ✅ Get the actual Branch object
    except Branch.DoesNotExist:
        return Response({'error': 'Invalid branch ID'}, status=400)

    user = CustomUser.objects.create_user(
        username=username,
        password=password,
        role=role,
        branch=branch  # ✅ Pass the Branch object, not just the ID
    )

    return Response({'message': 'User registered successfully'})