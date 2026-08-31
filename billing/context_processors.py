from .models import Category


def sidebar_categories(request):
    """Provide categories to the sidebar on every page."""

    return {
        "sidebar_categories": Category.objects.all()[:8],
    }
