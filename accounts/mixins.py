class SchoolAccessMixin:
    def get_queryset(self):
        qs = super().get_queryset()
        if hasattr(self.request.user, 'school'):
            return qs.filter(school=self.request.user.school)
        return qs 