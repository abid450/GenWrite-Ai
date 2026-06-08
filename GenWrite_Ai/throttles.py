from rest_framework.throttling import UserRateThrottle, AnonRateThrottle


class BurstRateThrottle(UserRateThrottle):
    rate = '20/min'
    scope = 'burst'



class SustainedRateThrottle(UserRateThrottle):
    rate = '200/day'
    scope = 'Sustained'



class ConatentGenerationThrottle(UserRateThrottle):
    rate = '10/min'
    scope = 'content_generation'



class BulkGenerationThrottle(UserRateThrottle):
    """Throttle for bulk generation"""
    rate = '5/hour'
    scope = 'bulk_generation'


class AnonContentThrottle(AnonRateThrottle):
    """Throttle for anonymous users"""
    rate = '5/min'
    scope = 'anon_content'