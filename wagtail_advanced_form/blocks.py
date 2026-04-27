from wagtail import blocks
from wagtail.blocks import PageChooserBlock


class AdvancedFormPageChooserBlock(blocks.StructBlock):
    form = PageChooserBlock('wagtail_advanced_form.AdvancedFormPage')

    class Meta:
        label = "Advanced Form Page"
        icon = "snippet"
        template = "wagtail_advanced_form/blocks/advanced_form_page_chooser_block.html"
