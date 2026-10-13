import frappe

try:
    from wiki.frappe_wiki.doctype.wiki_document.wiki_document import WikiDocument
    from wiki.permissions import can_read_space
except ImportError:
    WikiDocument = object
    can_read_space = lambda space: True


class TenantSafeWikiDocument(WikiDocument):
    """
    Ensures the Wiki Space switcher dropdown in the reader only displays
    spaces that the current logged-in user has permission to read.
    Prevents cross-tenant space leakage.
    """
    def get_web_context(self, *args, **kwargs):
        ctx = super().get_web_context(*args, **kwargs)
        if ctx and "wiki_spaces_for_switcher" in ctx:
            ctx["wiki_spaces_for_switcher"] = [
                s for s in ctx["wiki_spaces_for_switcher"] if can_read_space(s.name)
            ]
        return ctx
