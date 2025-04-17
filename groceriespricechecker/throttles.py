from rest_framework.throttling import SimpleRateThrottle

# Custom throttle class to limit forgot password requests
class FixedIntervalForgotPasswordThrottle(SimpleRateThrottle):
    scope = 'forgot_password'  # Scope for the throttle, used for caching

    # Define the rate limit as 1 request per 30 seconds
    def get_rate(self):
        return (1, 30)

    # Parse the rate if it's provided as a tuple
    def parse_rate(self, rate):
        if isinstance(rate, tuple):
            return rate
        return super().parse_rate(rate)

    # Generate a cache key based on the user's email
    def get_cache_key(self, request, view):
        if request.method == 'POST':
            email = request.data.get('email')
            if email:
                return self.cache_format % {
                    'scope': self.scope,
                    'ident': email.lower(),  # Use the email (case-insensitive) as the identifier
                }
        return None
