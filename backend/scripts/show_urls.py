from django.urls import get_resolver, URLPattern, URLResolver

def list_urls(urlpatterns, prefix=''):
    for pattern in urlpatterns:
        if isinstance(pattern, URLPattern):  # A single path
            print(prefix + str(pattern.pattern))
        elif isinstance(pattern, URLResolver):  # An included URLconf
            list_urls(pattern.url_patterns, prefix + str(pattern.pattern))

if __name__ == "__main__":
    resolver = get_resolver()
    list_urls(resolver.url_patterns)