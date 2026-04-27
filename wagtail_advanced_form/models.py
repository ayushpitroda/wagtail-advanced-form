from django.db import models
from modelcluster.fields import ParentalKey
from wagtail.admin.panels import (
    FieldPanel, FieldRowPanel,
    InlinePanel, MultiFieldPanel
)
from wagtail.models import Collection, Orderable
from wagtail.fields import RichTextField
from wagtail.contrib.forms.models import AbstractEmailForm, AbstractFormField, FORM_FIELD_CHOICES
from modelcluster.models import ClusterableModel
from wagtail.contrib.forms.utils import get_field_clean_name
import json
from wagtailcaptcha.forms import WagtailCaptchaFormBuilder
from wagtailcaptcha.models import WagtailCaptchaEmailForm
from wagtail.images.fields import WagtailImageField
from django.forms import FileField, CharField
from django import forms
from os.path import splitext
from wagtail.images.fields import WagtailImageField
from django.core.serializers.json import DjangoJSONEncoder
from wagtail.images import get_image_model
from wagtail.documents import get_document_model
from django.utils.html import format_html
from django.urls import reverse
from django.forms import FileField, CharField, ChoiceField
from django import forms
from wagtail.contrib.forms.views import SubmissionsListView
from django.utils.html import strip_tags
from django.core.mail import EmailMultiAlternatives
from django.template import Context, Template
from django.conf import settings
import re


def is_email_valid(email):
    """Basic email validation helper."""
    pattern = r'^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


class AdvancedFormBuilder(WagtailCaptchaFormBuilder):
    def create_image_field(self, field, options):
        return WagtailImageField(**options)

    def create_document_field(self, field, options):
        return FileField(**options)

    def create_heading_field(self, field, options):
        return CharField(widget=forms.HiddenInput(attrs={'data_type': 'heading'}), **options)


class AdvancedSubmissionsListView(SubmissionsListView):

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        if not self.is_export:
            field_types = ['submission_date'] + \
                [field.field_type for field in self.form_page.get_form_fields()]
            data_rows = context['data_rows']

            ImageModel = get_image_model()
            DocumentModel = get_document_model()

            for data_row in data_rows:
                fields = data_row['fields']

                for idx, (value, field_type) in enumerate(zip(fields, field_types)):
                    if field_type == 'image' and value:
                        image = ImageModel.objects.get(pk=value)
                        rendition = image.get_rendition('fill-100x75|jpegquality-40')
                        preview_url = rendition.url
                        url = reverse('wagtailimages:edit', args=(image.id,))
                        fields[idx] = format_html(
                            "<a href='{}'><img alt='Uploaded image - {}' src='{}' /></a>",
                            url,
                            image.title,
                            preview_url,
                        )
                    elif field_type == 'document' and value:
                        document = DocumentModel.objects.get(pk=value)
                        url = reverse('wagtaildocs:edit', args=(document.id,))
                        fields[idx] = format_html(
                            "<a href='{}'>{}</a>",
                            url,
                            document.title,
                        )

        return context


class Condition(models.Model):
    form_field = ParentalKey(
        'FormField',
        related_name='conditions',
        on_delete=models.CASCADE
    )

    OPERATOR_CHOICES = [
        ('empty', 'Is Empty'),
        ('not_empty', 'Is Not Empty'),
        ('equals', '='),
        ('not_equals', '!='),
        ('gt', '>'),
        ('gte', '>='),
        ('lt', '<'),
        ('lte', '<='),
    ]

    field_name = models.CharField(max_length=255)
    operator = models.CharField(max_length=20, choices=OPERATOR_CHOICES, verbose_name='Rule')
    value = models.CharField(max_length=255)

    panels = [
        FieldPanel('field_name'),
        FieldPanel('operator'),
        FieldPanel('value'),
    ]

    def __str__(self):
        return f"{self.field_name} {self.operator} {self.value}"


class FormField(AbstractFormField, ClusterableModel):
    field_type = models.CharField(
        verbose_name='field type',
        max_length=16,
        choices=list(FORM_FIELD_CHOICES) + [
            ('image', 'Upload Image'),
            ('document', 'File Upload'),
            ('heading', 'Heading'),
        ]
    )
    rule_action = models.CharField(
        max_length=10,
        choices=[('show', 'Show'), ('hide', 'Hide')],
        blank=True,
        null=True,
    )

    CONDITION_LOGIC_CHOICES = [
        ('and', 'Match ALL conditions (AND)'),
        ('or', 'Match ANY condition (OR)'),
    ]

    condition_logic = models.CharField(
        max_length=3,
        choices=CONDITION_LOGIC_CHOICES,
        default='and',
        help_text="How multiple conditions should be evaluated",
    )

    autoresponder_email_field = models.BooleanField("Autoresponder email field", default=False)
    autoresponder_salutation_field = models.BooleanField("Autoresponder salutation field", default=False)
    autoresponder_first_name_field = models.BooleanField("Autoresponder first name field", default=False)
    autoresponder_last_name_field = models.BooleanField("Autoresponder last name field", default=False)

    panels = AbstractFormField.panels + [
        MultiFieldPanel([
            FieldRowPanel([
                FieldPanel('autoresponder_email_field', classname='col6'),
                FieldPanel('autoresponder_salutation_field', classname='col6'),
            ]),
            FieldRowPanel([
                FieldPanel('autoresponder_first_name_field', classname='col6'),
                FieldPanel('autoresponder_last_name_field', classname='col6'),
            ]),
        ]),
        MultiFieldPanel([
            FieldPanel('rule_action'),
            FieldPanel('condition_logic'),
            InlinePanel('conditions', label="Conditions", panels=[
                FieldPanel('field_name'),
                FieldPanel('operator'),
                FieldPanel('value'),
            ])
        ], heading="Conditional Logic"),
    ]

    page = ParentalKey('AdvancedFormPage', on_delete=models.CASCADE, related_name='advanced_form_fields')


class AdvancedFormPage(WagtailCaptchaEmailForm):
    form_builder = AdvancedFormBuilder
    submissions_list_view_class = AdvancedSubmissionsListView
    thank_you_text = RichTextField(blank=True)

    autoresponder_from_email = models.CharField(max_length=100, null=True, blank=True)
    autoresponder_subject = models.CharField(max_length=200, null=True, blank=True)
    autoresponder_content = RichTextField(blank=True)

    content_panels = AbstractEmailForm.content_panels + [
        InlinePanel('advanced_form_fields'),
        FieldPanel('thank_you_text'),
        MultiFieldPanel([
            FieldRowPanel([
                FieldPanel('from_address', classname="col6"),
                FieldPanel('to_address', classname="col6"),
            ]),
            FieldPanel('subject'),
        ], "Email"),
        MultiFieldPanel([
            FieldRowPanel([
                FieldPanel('autoresponder_from_email', classname="col6"),
                FieldPanel('autoresponder_subject', classname="col6"),
            ]),
            FieldPanel('autoresponder_content'),
        ], "Autoresponder Email Config"),
    ]

    class Meta:
        verbose_name = "Advanced Form Page"

    def get_context(self, request):
        context = super().get_context(request)
        form = self.get_form(request.POST or None)
        context['form'] = form
        context['conditional_rules'] = json.dumps(self.get_conditional_rules())
        return context

    def get_conditional_rules(self):
        rules = []
        for field in self.get_form_fields():
            if field.rule_action:
                conditions = []
                for cond in field.conditions.all():
                    conditions.append({
                        "field": get_field_clean_name(cond.field_name),
                        "field_label": get_field_clean_name(field.label),
                        "operator": cond.operator,
                        "value": cond.value,
                    })
                if conditions:
                    rules.append({
                        "target": field.clean_name,
                        "field_label": get_field_clean_name(field.label),
                        "action": field.rule_action,
                        "conditions": conditions,
                        "condition_logic": field.condition_logic,
                    })
        return rules

    def get_form_fields(self):
        return self.advanced_form_fields.all()

    def get_uploaded_image_collection(self):
        """
        Returns a Wagtail Collection for uploaded files.
        Uses a collection named 'uploads' if it exists, otherwise returns root.
        You can override WAGTAIL_ADVANCED_FORM_UPLOAD_COLLECTION in settings
        to specify a different collection name.
        """
        collection_name = getattr(settings, 'WAGTAIL_ADVANCED_FORM_UPLOAD_COLLECTION', 'uploads')
        try:
            collection = Collection.objects.get(name__exact=collection_name)
            return collection
        except Collection.DoesNotExist:
            return Collection.get_first_root_node()

    @staticmethod
    def get_image_title(filename):
        """Generates a usable title from the filename of an upload."""
        if filename:
            result = splitext(filename)[0]
            result = result.replace('-', ' ').replace('_', ' ')
            return result.title()
        return ''

    def process_form_submission(self, form):
        cleaned_data = form.cleaned_data
        document_list = []
        images_list = []

        for name, field in form.fields.items():
            if isinstance(field, WagtailImageField):
                image_file_data = cleaned_data[name]
                if image_file_data:
                    ImageModel = get_image_model()
                    kwargs = {
                        'file': cleaned_data[name],
                        'title': self.get_image_title(cleaned_data[name].name),
                        'collection': self.get_uploaded_image_collection(),
                    }
                    if form.user and not form.user.is_anonymous:
                        kwargs['uploaded_by_user'] = form.user
                    image = ImageModel(**kwargs)
                    image.save()
                    cleaned_data.update({name: image.pk})
                    images_list.append(image.pk)
                else:
                    del cleaned_data[name]

            elif isinstance(field, FileField):
                document_file_data = cleaned_data[name]
                if document_file_data:
                    DocumentModel = get_document_model()
                    kwargs = {
                        'file': cleaned_data[name],
                        'title': self.get_image_title(cleaned_data[name].name),
                        'collection': self.get_uploaded_image_collection(),
                    }
                    if form.user and not form.user.is_anonymous:
                        kwargs['uploaded_by_user'] = form.user
                    document = DocumentModel(**kwargs)
                    document.save()
                    document_list.append(document.pk)
                    cleaned_data.update({name: document.pk})
                else:
                    del cleaned_data[name]

        submission = self.get_submission_class().objects.create(
            form_data=form.cleaned_data,
            page=self,
        )
        self.send_autoresponder(form)
        self.send_mail(form, document_list, images_list)
        return submission

    def send_mail(self, form, document_list, images_list):
        addresses = [x.strip() for x in self.to_address.split(',')]
        content = []
        for field in form:
            value = field.value()
            if isinstance(value, list):
                value = ', '.join(value)

            regular_field = True
            for n, f in form.fields.items():
                if isinstance(f, FileField) and field.name == n:
                    regular_field = False

            if regular_field and field.name != 'wagtailcaptcha':
                content.append('<p><strong>{}:</strong> {}</p>'.format(field.label, value))

        site_url = getattr(settings, 'WAGTAIL_ADVANCED_FORM_SITE_URL',
                           getattr(settings, 'SITE_URL', ''))

        try:
            for f in images_list:
                ImageModel = get_image_model()
                image_file = ImageModel.objects.get(pk=f)
                if image_file:
                    rendition = image_file.get_rendition('original')
                    _ = site_url + rendition.url
        except Exception:
            pass

        try:
            for f in document_list:
                DocumentModel = get_document_model()
                document = DocumentModel.objects.get(pk=f)
                if document:
                    _ = site_url + document.url
        except Exception:
            pass

        content = '\n'.join(content)
        content = content.replace("<br>", "").replace("<br />", "")
        text_content = strip_tags(content)
        if self.from_address and addresses:
            mail = EmailMultiAlternatives(self.subject, text_content, self.from_address, addresses)
            if content:
                mail.attach_alternative(content, 'text/html')
            mail.send()

    def send_autoresponder(self, form):
        auto_responder_field = self.advanced_form_fields.filter(autoresponder_email_field=True).first()
        salutation = self.advanced_form_fields.filter(autoresponder_salutation_field=True).first()
        first_name = self.advanced_form_fields.filter(autoresponder_first_name_field=True).first()
        last_name = self.advanced_form_fields.filter(autoresponder_last_name_field=True).first()
        salutation_value = form.cleaned_data.get(salutation.clean_name) if salutation else ""
        first_name_value = form.cleaned_data.get(first_name.clean_name) if first_name else ""
        last_name_value = form.cleaned_data.get(last_name.clean_name) if last_name else ""

        if self.autoresponder_from_email and auto_responder_field:
            from_address = self.autoresponder_from_email.strip()
            html = self.autoresponder_content
            context = {
                'salutation': salutation_value,
                'first_name': first_name_value,
                'last_name': last_name_value,
            }
            html_content = Template(html).render(Context(context))
            text_content = strip_tags(html_content)
            auto_field_name = auto_responder_field.clean_name
            to_email = form.cleaned_data.get(auto_field_name)
            if to_email and is_email_valid(to_email):
                mail = EmailMultiAlternatives(
                    self.autoresponder_subject, text_content, from_address, [to_email]
                )
                if html_content:
                    mail.attach_alternative(html_content, 'text/html')
                mail.send(fail_silently=True)
