from django.core.exceptions import ValidationError

class ExactLengthValidator:
    def __init__(self, length=8):
        self.length = int(length)

    def validate(self, password, user=None):
        if len(password) != self.length:
            raise ValidationError(
                f"The password must be only {self.length} characters long.",
                code="password_exact_length",
            )

    def get_help_text(self):
        return f"Your password must be only {self.length} characters long."
