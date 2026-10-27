def course_context(request):
    if not request.user.is_authenticated:
        return {"count": 0, "cart_count": 0}
    user = request.user
    initials = ((user.first_name[:1] + user.last_name[:1]) or user.username[:2]).upper()
    return {
        "count": user.purchase.filter(is_paid=True).values('course_objects').distinct().count(),
        "cart_count": user.basket.count(),
        "profile_initials": initials,
    }
