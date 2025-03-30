from rest_framework.throttling import SimpleRateThrottle

class FixedIntervalForgotPasswordThrottle(SimpleRateThrottle):
    scope = 'forgot_password'

    def get_rate(self):
        return (1, 30)

    def parse_rate(self, rate):
        if isinstance(rate, tuple):
            return rate
        return super().parse_rate(rate)

    def get_cache_key(self, request, view):
        if request.method == 'POST':
            email = request.data.get('email')
            if email:
                return self.cache_format % {
                    'scope': self.scope,
                    'ident': email.lower(),
                }
        return None
