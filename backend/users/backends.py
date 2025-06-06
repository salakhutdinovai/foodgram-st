from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from django.db.models import Q

User = get_user_model()

class EmailBackend(ModelBackend):
    def authenticate(self, request, email=None, password=None, **kwargs):
        print(f"Debug: EmailBackend.authenticate called with email={email}, password={password}")
        try:
            user = User.objects.get(Q(email__iexact=email))
            print(f"Debug: Found user: {user}")
            print(f"Debug: Stored password hash: {user.password}")
            if user.check_password(password):
                print("Debug: Password is correct")
                return user
            else:
                print("Debug: Password is incorrect")
        except User.DoesNotExist:
            print("Debug: User not found")
        return None

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None