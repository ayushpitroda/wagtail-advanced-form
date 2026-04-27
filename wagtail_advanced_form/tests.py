from django.test import TestCase


class WagtailAdvancedFormTests(TestCase):
    def test_import(self):
        from wagtail_advanced_form.models import AdvancedFormPage, FormField, Condition
        from wagtail_advanced_form.blocks import AdvancedFormPageChooserBlock
        self.assertTrue(True)
