import contextlib

from django.utils.deprecation import MiddlewareMixin


class PutPatchWithFileFormMiddleware(MiddlewareMixin):
    def process_request(self, request):
        if (
            request.method not in ("PUT", "PATCH")
            or request.content_type == "application/json"
        ):
            return None
        if hasattr(request, "_post"):
            del request._post
            del request._files
        with contextlib.suppress(Exception):
            self._extracted_from_process_request_(request)

    def _extracted_from_process_request_(self, request):
        initial_method = request.method
        request.method = "POST"
        request.META["REQUEST_METHOD"] = "POST"
        request._load_post_and_files()
        request.META["REQUEST_METHOD"] = initial_method
        request.method = initial_method
