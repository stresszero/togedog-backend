from django.utils.deprecation import MiddlewareMixin


class PutPatchWithFileFormMiddleware(MiddlewareMixin):
    def process_request(self, request):
        if (
            request.method not in ("PUT", "PATCH")
            or request.content_type == "application/json"
        ):
            return
        if hasattr(request, "_post"):
            del request._post
            del request._files
        try:
            initial_method = request.method
            request.method = "POST"
            request.META["REQUEST_METHOD"] = "POST"
            request._load_post_and_files()
            request.META["REQUEST_METHOD"] = initial_method
            request.method = initial_method
        except Exception:
            pass
