from rest_framework.throttling import ScopedRateThrottle


class UploadRateThrottle(ScopedRateThrottle):
    """Throttle applied only to image-upload actions.

    ``ScopedRateThrottle`` normally reads ``view.throttle_scope``; returning the
    scope explicitly lets us attach a stricter limit to a single action without
    throttling every other action on the same viewset.
    """

    def get_throttle_scope(self):
        return 'upload'