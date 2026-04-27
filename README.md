# wagtail-advanced-form

A reusable Wagtail app that extends the built-in form builder with:

- **Conditional logic** — show/hide fields based on other field values (AND / OR)
- **Image upload** fields — saves directly to Wagtail image library
- **File / document upload** fields — saves to Wagtail document library
- **Heading** fields — static section headers inside your form
- **Autoresponder emails** — send a personalised reply to the submitter
- **reCAPTCHA** support (via `wagtail-django-recaptcha`)
- **Reusable block** — embed a form on any page via `AdvancedFormPageChooserBlock`

---

## Requirements

| Dependency | Version |
|---|---|
| Python | ≥ 3.10 |
| Django | ≥ 4.2 |
| Wagtail | ≥ 5.0 |
| django-modelcluster | ≥ 6.0 |
| wagtail-django-recaptcha | ≥ 1.0 |

---

## Installation

### 1. Install the package

```bash
pip install wagtail-advanced-form
```

Or install directly from source:

```bash
pip install git+https://github.com/yourusername/wagtail-advanced-form.git
```

Or in development / editable mode from a local clone:

```bash
git clone https://github.com/yourusername/wagtail-advanced-form.git
pip install -e wagtail-advanced-form/
```

### 2. Add to `INSTALLED_APPS`

```python
# settings.py

INSTALLED_APPS = [
    # ... your existing apps ...
    'wagtail.contrib.forms',
    'wagtailcaptcha',          # wagtail-django-recaptcha
    'wagtail_advanced_form',   # ← add this
]
```

### 3. Configure reCAPTCHA

In your `settings.py` add your Google reCAPTCHA v2 keys:

```python
RECAPTCHA_PUBLIC_KEY  = 'your-site-key'
RECAPTCHA_PRIVATE_KEY = 'your-secret-key'
NOCAPTCHA = True  # use reCAPTCHA v2 checkbox style
```

### 4. (Optional) Configure the upload collection

By default uploaded images and documents are stored in a Wagtail collection
named **"uploads"**. You can override this:

```python
# settings.py
WAGTAIL_ADVANCED_FORM_UPLOAD_COLLECTION = 'Form Uploads'
```

If the named collection does not exist the root collection is used as a fallback.

### 5. (Optional) Configure site URL for email links

```python
# settings.py
WAGTAIL_ADVANCED_FORM_SITE_URL = 'https://www.yoursite.com'
# Or the existing SITE_URL setting is used automatically if present.
```

### 6. Run migrations

```bash
python manage.py migrate wagtail_advanced_form
```

---

## Usage

### As a standalone page type

`AdvancedFormPage` is a Wagtail page type you can add to your page tree just like
any other page.  It appears in the Wagtail admin under **Add child page**.

The app ships with a default template at:

```
wagtail_advanced_form/templates/wagtail_advanced_form/advanced_form_page.html
```

To override the template, create your own at the same path inside your project's
`templates/` directory.

### As an embeddable block on other pages

Use `AdvancedFormPageChooserBlock` to embed a form inside any StreamField:

```python
# your_app/models.py

from wagtail.fields import StreamField
from wagtail_advanced_form.blocks import AdvancedFormPageChooserBlock

class MyLandingPage(Page):
    body = StreamField([
        ('advanced_form', AdvancedFormPageChooserBlock()),
        # ... other blocks ...
    ])
```

Then in your template, load the tag library and render the block normally:

```html
{% load wagtailcore_tags advanced_form_tags %}

{% for block in page.body %}
    {% include_block block %}
{% endfor %}
```

The block template is at:

```
wagtail_advanced_form/templates/wagtail_advanced_form/blocks/advanced_form_page_chooser_block.html
```

### Template tags

```html
{% load advanced_form_tags %}

{# Lowercase a label to match clean_name format #}
{{ field.label|clean_label }}

{# Render a form inside any template (for block use) #}
{% get_form_context form_page as form_fields %}
```

---

## Settings Reference

| Setting | Default | Description |
|---|---|---|
| `WAGTAIL_ADVANCED_FORM_UPLOAD_COLLECTION` | `"uploads"` | Wagtail collection name for uploaded files |
| `WAGTAIL_ADVANCED_FORM_SITE_URL` | `SITE_URL` or `""` | Base URL prepended to file links in notification emails |
| `RECAPTCHA_PUBLIC_KEY` | — | Google reCAPTCHA site key |
| `RECAPTCHA_PRIVATE_KEY` | — | Google reCAPTCHA secret key |
| `NOCAPTCHA` | `True` | Use v2 checkbox reCAPTCHA |

---

## Customising Templates

All templates use standard Django/Wagtail template tags and currently reference
class names from a custom CSS framework. You will likely want to override them
to match your project's design system.

Copy the templates into your project's `templates/` directory preserving the
`wagtail_advanced_form/` namespace:

```
your_project/
└── templates/
    └── wagtail_advanced_form/
        ├── advanced_form_page.html
        └── blocks/
            └── advanced_form_page_chooser_block.html
```

---

## Migrating from the old `advanced_form` app

If you were using this as an internal app named `advanced_form`:

1. Install the package and add `wagtail_advanced_form` to `INSTALLED_APPS`.
2. Remove `advanced_form` from `INSTALLED_APPS`.
3. Create a **data migration** in your project to rename the Django content types and rename the DB tables:

```bash
python manage.py migrate --fake wagtail_advanced_form 0005
```

> **Important:** If you have existing data you must rename the tables manually
> or write a migration. Contact the maintainer for a migration guide.

---

## Development

```bash
git clone https://github.com/yourusername/wagtail-advanced-form.git
cd wagtail-advanced-form
pip install -e ".[dev]"
```

Run tests:

```bash
pytest
```

---

## Changelog

### 1.0.0 (2026-04-27)
- Initial public release as installable PyPI package
- Extracted from project-specific `advanced_form` Django app
- Added `WAGTAIL_ADVANCED_FORM_UPLOAD_COLLECTION` and `WAGTAIL_ADVANCED_FORM_SITE_URL` settings
- Removed hard dependency on project-level `pages.utils.is_email_valid` — bundled inline

---

## License

MIT — see [LICENSE](LICENSE).
"# wagtail-advanced-form" 
