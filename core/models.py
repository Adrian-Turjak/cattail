
from django.db import models
from django.utils.timezone import now
from django.shortcuts import redirect

from wagtail.wagtailcore.models import Page, Orderable
from wagtail.wagtailcore.fields import RichTextField
from wagtail.wagtailforms.edit_handlers import FormSubmissionsPanel
from wagtail.wagtailadmin.edit_handlers import (
    FieldPanel, MultiFieldPanel, FieldRowPanel,
    InlinePanel, PageChooserPanel)
from wagtail.wagtailimages.edit_handlers import ImageChooserPanel
from wagtail.wagtaildocs.edit_handlers import DocumentChooserPanel
from wagtail.wagtailforms.models import AbstractFormField
from wagtail.wagtailsearch import index

from wagtailcaptcha.models import WagtailCaptchaEmailForm

from modelcluster.fields import ParentalKey


# A couple of abstract classes that contain commonly used fields

class LinkFields(models.Model):
    link_page = models.ForeignKey(
        'wagtailcore.Page',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+'
    )
    link_document = models.ForeignKey(
        'wagtaildocs.Document',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+'
    )
    link_external = models.URLField("External link", blank=True)

    @property
    def link(self):
        if self.link_page:
            return self.link_page.url
        elif self.link_document:
            return self.link_document.url
        else:
            return self.link_external

    panels = [
        PageChooserPanel('link_page'),
        DocumentChooserPanel('link_document'),
        FieldPanel('link_external'),
    ]

    class Meta:
        abstract = True


class NoteFields(models.Model):
    note = RichTextField()
    image = models.ForeignKey(
        'wagtailimages.Image',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+'
    )
    document = models.ForeignKey(
        'wagtaildocs.Document',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+'
    )
    noted_at = models.DateTimeField(default=now)

    panels = [
        FieldPanel('note'),
        FieldPanel('noted_at'),
    ]

    class Meta:
        abstract = True


# Carousel items

class CarouselItem(LinkFields):
    image = models.ForeignKey(
        'wagtailimages.Image',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+'
    )
    caption = models.CharField(max_length=255, blank=True)

    panels = [
        ImageChooserPanel('image'),
        FieldPanel('caption'),
        MultiFieldPanel(LinkFields.panels, "Link"),
    ]

    class Meta:
        abstract = True


# Related links

class RelatedLink(LinkFields):
    title = models.CharField(max_length=255, help_text="Link title")

    panels = [
        FieldPanel('title'),
        MultiFieldPanel(LinkFields.panels, "Link"),
    ]

    class Meta:
        abstract = True


# Redirect page

class RedirectPage(Page, LinkFields):

    def serve(self, request):
        return redirect(self.link, permanent=False)

    content_panels = [FieldPanel('title')] + LinkFields.panels


# Home Page

class HomePageCarouselItem(Orderable, CarouselItem):
    page = ParentalKey('core.HomePage', related_name='carousel_items')


class HomePageNotes(Orderable, NoteFields):
    page = ParentalKey('core.HomePage', related_name='notes')


class HomePage(Page):
    content = RichTextField(blank=True)
    search_fields = Page.search_fields + [
        index.SearchField('content'),
    ]

    class Meta:
        verbose_name = "Homepage"

    content_panels = [
        FieldPanel('title', classname="full title"),
        FieldPanel('content'),
        InlinePanel('carousel_items', label="Carousel items"),
        InlinePanel('notes', label="Notes (not publically visible)"),
    ]

    promote_panels = Page.promote_panels


# Article index page

class ArticleIndexPageRelatedLink(Orderable, RelatedLink):
    page = ParentalKey('core.ArticleIndexPage', related_name='related_links')


class ArticleIndexPageNotes(Orderable, NoteFields):
    page = ParentalKey('core.ArticleIndexPage', related_name='notes')


class ArticleIndexPage(Page):
    intro = RichTextField(blank=True)
    index_image = models.ForeignKey(
        'wagtailimages.Image',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+'
    )

    search_fields = Page.search_fields + [
        index.SearchField('intro'),
    ]

    subpage_types = [
        'ArticlePage', 'ArticleIndexPage', 'ArticleIndexWithImagePage',
        'AnimalDetailIndexPage', 'AnimalLitterIndexPage', 'AnimalDetailPage',
        'FormPage']

    content_panels = [
        FieldPanel('title', classname="full title"),
        FieldPanel('intro', classname="full"),
        InlinePanel('related_links', label="Related links"),
        InlinePanel('notes', label="Notes (not publically visible)"),
    ]
    promote_panels = Page.promote_panels + [
        ImageChooserPanel('index_image'),
    ]


class NewsArticleIndexPage(ArticleIndexPage):
    news_list_style = models.CharField(max_length=255, choices=(
        ('title_intro_link', 'Articles with title and intro with link.'),
        ('full_no_link', 'Full articles with no link.')))

    subpage_types = ['NewsArticlePage']

    # NOTE(adriant): Using odd array slicing to stick this right after
    # the title field.
    content_panels = ArticleIndexPage.content_panels[0:1] + [
        FieldPanel('news_list_style', classname="News list style."),
    ] + ArticleIndexPage.content_panels[1:]


# Article index with image page

class ArticleIndexWithImagePage(ArticleIndexPage):
    image = models.ForeignKey(
        'wagtailimages.Image',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+'
    )
    show_placeholder = models.BooleanField()

    content_panels = ArticleIndexPage.content_panels + [
        ImageChooserPanel('image'),
        FieldPanel('show_placeholder', classname="Show placeholder image."),
    ]


# Article page

class ArticlePageRelatedLink(Orderable, RelatedLink):
    page = ParentalKey('core.ArticlePage', related_name='related_links')


class ArticlePageNotes(Orderable, NoteFields):
    page = ParentalKey('core.ArticlePage', related_name='notes')


class ArticlePage(Page):
    intro = RichTextField(blank=True)
    body = RichTextField(blank=True)
    index_image = models.ForeignKey(
        'wagtailimages.Image',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+'
    )

    search_fields = Page.search_fields + [
        index.SearchField('intro'),
        index.SearchField('body'),
    ]

    content_panels = [
        FieldPanel('title', classname="full title"),
        FieldPanel('intro', classname="full"),
        FieldPanel('body', classname="full"),
        InlinePanel('related_links', label="Related links"),
        InlinePanel('notes', label="Notes (not publically visible)"),
    ]
    promote_panels = Page.promote_panels + [
        ImageChooserPanel('index_image'),
    ]


class NewsArticlePage(ArticlePage):
    date = models.DateTimeField(default=now)

    # NOTE(adriant): Using odd array slicing to stick this right after
    # the title field.
    content_panels = ArticlePage.content_panels[0:1] + [
        FieldPanel('date', classname="Date"),
    ] + ArticlePage.content_panels[1:]


# Animal Detail Index Page

class AnimalDetailIndexPage(ArticleIndexWithImagePage):
    subpage_types = ['AnimalDetailPage']


# Animal Details page

class AnimalDetailSireLink(LinkFields):
    name = models.CharField(max_length=255)
    link_page = models.ForeignKey(
        'core.AnimalDetailPage',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+'
    )
    page = ParentalKey(
        'core.AnimalDetailPage',
        related_name='sire_link',
        unique=True
    )

    panels = [FieldPanel('name'), ] + LinkFields.panels


class AnimalDetailDamLink(LinkFields):
    name = models.CharField(max_length=255)
    link_page = models.ForeignKey(
        'core.AnimalDetailPage',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+'
    )
    page = ParentalKey(
        'core.AnimalDetailPage',
        related_name='dam_link',
        unique=True
    )
    panels = [FieldPanel('name'), ] + LinkFields.panels


class AnimalDetailPedigreeLink(LinkFields):
    page = ParentalKey(
        'core.AnimalDetailPage',
        related_name='pedigree_link',
        unique=True
    )


class AnimalDetailPageRelatedLink(Orderable, RelatedLink):
    page = ParentalKey('core.AnimalDetailPage', related_name='related_links')


class AnimalDetailPageNotes(Orderable, NoteFields):
    page = ParentalKey('core.AnimalDetailPage', related_name='notes')


class AnimalDetailPage(Page):
    name = models.CharField(max_length=255)
    breed = models.CharField(max_length=255)
    sex = models.CharField(max_length=255, choices=(
        ('Male', 'Male'), ('Female', 'Female')))
    colour = models.CharField(max_length=255)
    date_of_birth = models.DateField()
    extra_info = RichTextField(blank=True)
    image = models.ForeignKey(
        'wagtailimages.Image',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+'
    )
    index_image = models.ForeignKey(
        'wagtailimages.Image',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+'
    )

    search_fields = Page.search_fields + [
        index.SearchField('name'),
        index.FilterField('breed'),
        index.FilterField('sex'),
        index.FilterField('colouring'),
        index.FilterField('date_of_birth'),
        index.SearchField('extra_info'),
    ]

    @property
    def sire(self):
        return self.sire_link.all().first()

    @property
    def dam(self):
        return self.dam_link.all().first()

    @property
    def pedigree(self):
        return self.pedigree_link.all().first()

    @property
    def litters(self):
        litters = []
        now_date = now().date()
        if self.sex == "Male":
            for litter in self.litters_sire.all():
                if litter.date_of_birth and litter.date_of_birth <= now_date:
                    litters.append(litter)
        elif self.sex == "Female":
            for litter in self.litters_dam.all():
                if litter.date_of_birth and litter.date_of_birth <= now_date:
                    litters.append(litter)
        return litters

    content_panels = [
        FieldPanel('title', classname="full title"),
        ImageChooserPanel('image'),
        MultiFieldPanel(
            [
                FieldPanel('name'),
                FieldPanel('sex'),
                FieldPanel('breed'),
                FieldPanel('colour'),
                FieldPanel('date_of_birth'),
            ], "Details"),
        InlinePanel('sire_link', label="Sire"),
        InlinePanel('dam_link', label="Dam"),
        InlinePanel('pedigree_link', label="Pedigree"),
        FieldPanel('extra_info', classname="full"),
        InlinePanel('related_links', label="Related links"),
        InlinePanel('notes', label="Notes (not publically visible)"),
    ]

    promote_panels = Page.promote_panels + [
        ImageChooserPanel('index_image'),
    ]


# Animal Detail Index Page

class AnimalLitterIndexPage(ArticleIndexWithImagePage):
    subpage_types = ['AnimalLitterPage']


# Animal Litter page

class Juvenile(models.Model):
    name = models.CharField(max_length=255)
    sex = models.CharField(max_length=255, choices=(
        ('Male', 'Male'), ('Female', 'Female')))
    colour = models.CharField(max_length=255)
    birth_weight = models.CharField(max_length=255)
    status = models.CharField(max_length=255)
    extra_info = RichTextField(blank=True)
    image = models.ForeignKey(
        'wagtailimages.Image',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+'
    )
    parent = ParentalKey('core.AnimalLitterPage', related_name='juveniles')
    detail_page = models.ForeignKey(
        'core.AnimalDetailPage',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+'
    )

    @property
    def link(self):
        return self.detail_page.url

    panels = [
        MultiFieldPanel(
            [
                FieldPanel('name'),
                FieldPanel('sex'),
                FieldPanel('colour'),
                FieldPanel('birth_weight'),
                FieldPanel('status'),
            ], "Details"),
        FieldPanel('extra_info', classname="full"),
        ImageChooserPanel('image'),
        PageChooserPanel('detail_page'),
    ]


class AnimalLitterPedigreeLink(LinkFields):
    page = ParentalKey(
        'core.AnimalLitterPage',
        related_name='pedigree_link',
        unique=True
    )


class AnimalLitterPageRelatedLink(Orderable, RelatedLink):
    page = ParentalKey('core.AnimalLitterPage', related_name='related_links')


class AnimalLitterPageNotes(Orderable, NoteFields):
    page = ParentalKey('core.AnimalLitterPage', related_name='notes')


class AnimalLitterPage(Page):
    sire = models.ForeignKey(
        'core.AnimalDetailPage',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='litters_sire'
    )
    dam = models.ForeignKey(
        'core.AnimalDetailPage',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='litters_dam'
    )
    date_of_birth = models.DateField(null=True, blank=True)
    extra_info = RichTextField(blank=True)
    index_image = models.ForeignKey(
        'wagtailimages.Image',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+'
    )
    search_fields = Page.search_fields + [
        index.SearchField('extra_info'),
    ]

    @property
    def pedigree(self):
        return self.pedigree_link.all().first()

    content_panels = [
        FieldPanel('title', classname="full title"),
        PageChooserPanel('sire'),
        PageChooserPanel('dam'),
        FieldPanel('date_of_birth'),
        InlinePanel('pedigree_link', label="Pedigree"),
        FieldPanel('extra_info', classname="full"),
        InlinePanel('juveniles', label="Juveniles"),
        InlinePanel('related_links', label="Related links"),
        InlinePanel('notes', label="Notes (not publically visible)"),
    ]
    promote_panels = Page.promote_panels + [
        ImageChooserPanel('index_image'),
    ]


# Contact Page

class FormField(AbstractFormField):
    page = ParentalKey('FormPage', related_name='form_fields')


class FormPage(WagtailCaptchaEmailForm):
    intro = RichTextField(blank=True)
    thank_you_text = RichTextField(blank=True)

    content_panels = [
        FormSubmissionsPanel(),
        FieldPanel('title', classname="full title"),
        FieldPanel('intro', classname="full"),
        InlinePanel('form_fields', label="Form fields"),
        FieldPanel('thank_you_text', classname="full"),
        MultiFieldPanel([
            FieldRowPanel([
                FieldPanel('from_address', classname="col6"),
                FieldPanel('to_address', classname="col6"),
            ]),
            FieldPanel('subject'),
        ], "Email"),
    ]
