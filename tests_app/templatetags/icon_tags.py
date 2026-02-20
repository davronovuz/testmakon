"""
TestMakon - 3D Subject Icons via Microsoft Fluent Emoji
Hamma qurilmada bir xil ko'rinadi (PNG rasm sifatida yukladi)
"""

from django import template
from django.utils.html import format_html

register = template.Library()

# Microsoft Fluent Emoji 3D CDN (jsDelivr)
CDN = "https://cdn.jsdelivr.net/gh/microsoft/fluentui-emoji@main/assets/"

# Har bir fan slugiga mos Fluent Emoji 3D icon
SUBJECT_ICONS = {
    'matematika':            'Abacus/3D/abacus_3d.png',
    'fizika':                'High%20voltage/3D/high_voltage_3d.png',
    'kimyo':                 'Test%20tube/3D/test_tube_3d.png',
    'biologiya':             'Dna/3D/dna_3d.png',
    'ona-tili-va-adabiyot':  'Books/3D/books_3d.png',
    'ona-tili':              'Books/3D/books_3d.png',
    'adabiyot':              'Scroll/3D/scroll_3d.png',
    'ingliz-tili':           'Globe%20with%20meridians/3D/globe_with_meridians_3d.png',
    'tarix':                 'Classical%20building/3D/classical_building_3d.png',
    'geografiya':            'Globe%20showing%20Europe-Africa/3D/globe_showing_europe-africa_3d.png',
    'informatika':           'Laptop/3D/laptop_3d.png',
    'huquqshunoslik':        'Balance%20scale/3D/balance_scale_3d.png',
    'iqtisodiyot':           'Chart%20increasing/3D/chart_increasing_3d.png',
    'rus-tili':              'Pencil/3D/pencil_3d.png',
    'nemis-tili':            'Graduation%20cap/3D/graduation_cap_3d.png',
    'fransuz-tili':          'Artist%20palette/3D/artist_palette_3d.png',
    'astronomiya':           'Ringed%20planet/3D/ringed_planet_3d.png',
    'chizmachilik':          'Triangular%20ruler/3D/triangular_ruler_3d.png',
    'sport':                 'Soccer%20ball/3D/soccer_ball_3d.png',
    'musiqa':                'Musical%20notes/3D/musical_notes_3d.png',
}

# UI icon lari uchun (sidebar, navbar, va h.k.)
UI_ICONS = {
    'test':         'Pencil/3D/pencil_3d.png',
    'trophy':       'Trophy/3D/trophy_3d.png',
    'star':         'Star/3D/star_3d.png',
    'fire':         'Fire/3D/fire_3d.png',
    'brain':        'Brain/3D/brain_3d.png',
    'rocket':       'Rocket/3D/rocket_3d.png',
    'target':       'Bullseye/3D/bullseye_3d.png',
    'clock':        'Alarm%20clock/3D/alarm_clock_3d.png',
    'chart':        'Bar%20chart/3D/bar_chart_3d.png',
    'medal':        'Sports%20medal/3D/sports_medal_3d.png',
    'crown':        'Crown/3D/crown_3d.png',
    'lightning':    'High%20voltage/3D/high_voltage_3d.png',
    'gem':          'Gem%20stone/3D/gem_stone_3d.png',
    'books':        'Books/3D/books_3d.png',
    'laptop':       'Laptop/3D/laptop_3d.png',
    'calendar':     'Calendar/3D/calendar_3d.png',
    'check':        'Check%20mark%20button/3D/check_mark_button_3d.png',
    'lock':         'Locked/3D/locked_3d.png',
    'unlock':       'Unlocked/3D/unlocked_3d.png',
    'shield':       'Shield/3D/shield_3d.png',
    'graduation':   'Graduation%20cap/3D/graduation_cap_3d.png',
    'magnifier':    'Magnifying%20glass%20tilted%20left/3D/magnifying_glass_tilted_left_3d.png',
    '1st':          '1st%20place%20medal/3D/1st_place_medal_3d.png',
    '2nd':          '2nd%20place%20medal/3D/2nd_place_medal_3d.png',
    '3rd':          '3rd%20place%20medal/3D/3rd_place_medal_3d.png',
}


@register.simple_tag
def subject_icon(subject, size=40):
    """
    Fan ikonasini 3D rasm sifatida ko'rsatish.
    Foydalanish: {% subject_icon subject 48 %}
    """
    if not subject:
        return format_html(
            '<span style="font-size:{}px;line-height:1;display:inline-block;">📚</span>',
            int(size * 0.75)
        )

    slug = getattr(subject, 'slug', '')
    fallback = getattr(subject, 'icon', '📚')
    name = getattr(subject, 'name', '')
    icon_path = SUBJECT_ICONS.get(slug)

    if icon_path:
        url = CDN + icon_path
        return format_html(
            '<img src="{}" width="{}" height="{}" alt="{}" '
            'loading="lazy" style="object-fit:contain;display:inline-block;vertical-align:middle;" '
            'onerror="this.style.display=\'none\';this.nextSibling.style.removeProperty(\'display\');">',
            url, size, size, name
        )

    # Fallback: emoji
    return format_html(
        '<span style="font-size:{}px;line-height:1;display:inline-block;">{}</span>',
        int(size * 0.75), fallback
    )


@register.simple_tag
def ui_icon(name, size=32):
    """
    UI ikonasini 3D rasm sifatida ko'rsatish.
    Foydalanish: {% ui_icon 'trophy' 40 %}
    """
    icon_path = UI_ICONS.get(name)
    if icon_path:
        url = CDN + icon_path
        return format_html(
            '<img src="{}" width="{}" height="{}" alt="{}" '
            'loading="lazy" style="object-fit:contain;display:inline-block;vertical-align:middle;">',
            url, size, size, name
        )
    return format_html('<span>🔹</span>')
