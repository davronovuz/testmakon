"""
TestMakon.uz — DTM 2026 SEO Maqolalari
Data migration: 6 ta DTM 2026 maqolasi + cover rasmlar
"""
import os
from django.db import migrations
from django.utils import timezone


# ─── Cover rasmlar yaratish ──────────────────────────────────────────────────

def _create_cover_image(filepath, bg_color_hex, title_line1, title_line2, icon_text):
    """Pillow yordamida cover rasm yaratadi"""
    try:
        from PIL import Image, ImageDraw, ImageFont

        W, H = 1200, 630

        # Hex → RGB
        h = bg_color_hex.lstrip('#')
        r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
        dark_r = max(0, r - 40)
        dark_g = max(0, g - 40)
        dark_b = max(0, b - 40)

        img = Image.new('RGB', (W, H), (r, g, b))
        draw = ImageDraw.Draw(img)

        # Gradient effect — pastki qism qoraytirish
        for y in range(H):
            alpha = y / H
            cr = int(r * (1 - alpha * 0.35) + dark_r * alpha * 0.35)
            cg = int(g * (1 - alpha * 0.35) + dark_g * alpha * 0.35)
            cb = int(b * (1 - alpha * 0.35) + dark_b * alpha * 0.35)
            draw.line([(0, y), (W, y)], fill=(cr, cg, cb))

        # Dekorativ doiralar (fill=None — faqat chegara, RGB mode uchun to'g'ri)
        draw.ellipse([W - 280, -120, W + 80, 240], fill=None,
                     outline=(255, 255, 255), width=2)
        draw.ellipse([W - 200, -60, W + 20, 160], fill=None,
                     outline=(255, 255, 255), width=1)
        draw.ellipse([-80, H - 200, 200, H + 80], fill=None,
                     outline=(255, 255, 255), width=2)

        # TestMakon.uz logo area
        draw.rectangle([56, 52, 56 + 200, 52 + 44], fill=None,
                       outline=(255, 255, 255), width=2)

        # Font yuklash
        font_paths = [
            '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',
            '/usr/share/fonts/truetype/freefont/FreeSansBold.ttf',
            '/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf',
            '/System/Library/Fonts/Helvetica.ttc',
            '/System/Library/Fonts/Arial.ttf',
        ]
        font_large = font_medium = font_small = font_brand = None
        for fp in font_paths:
            if os.path.exists(fp):
                try:
                    font_large = ImageFont.truetype(fp, 80)
                    font_medium = ImageFont.truetype(fp, 52)
                    font_small = ImageFont.truetype(fp, 32)
                    font_brand = ImageFont.truetype(fp, 28)
                    break
                except Exception:
                    pass

        if font_large is None:
            font_large = font_medium = font_small = font_brand = ImageFont.load_default()

        # TestMakon.uz branding
        draw.text((72, 60), "TestMakon.uz", fill=(255, 255, 255), font=font_brand)

        # Icon emoji (oddiy harf sifatida)
        draw.text((72, 180), icon_text, fill=(255, 255, 255), font=font_large)

        # Sarlavha
        draw.text((72, 310), title_line1, fill=(255, 255, 255), font=font_medium)
        if title_line2:
            draw.text((72, 380), title_line2, fill=(220, 255, 200), font=font_medium)

        # DTM 2026 badge
        badge_x, badge_y = 72, 490
        draw.rectangle([badge_x - 8, badge_y - 8, badge_x + 200, badge_y + 44],
                       fill=(255, 255, 255))
        draw.text((badge_x, badge_y), "DTM 2026", fill=(r, g, b), font=font_small)

        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        img.save(filepath, 'PNG', quality=95)
        return True

    except Exception as e:
        print(f"  [RASM XATO] {e} — rasm yaratilmadi, maqola rasmsiz saqlanadi")
        return False


# ─── Maqola ma'lumotlari ─────────────────────────────────────────────────────

ARTICLES = [
    {
        'slug': 'dtm-2026-toliq-tayyorgarlik-qollanmasi',
        'title': "DTM 2026 — To'liq Tayyorgarlik Qo'llanmasi",
        'meta_title': "DTM 2026 Tayyorgarligi: To'liq Qo'llanma | TestMakon.uz",
        'meta_description': "DTM 2026 imtihoniga qanday tayyorlanish kerak? Fanlar, vaqt rejasi, ball hisoblash — to'liq qo'llanma. TestMakon da bepul mashq qiling!",
        'excerpt': "DTM 2026 imtihoniga eng samarali tayyorlanish usullari. Qaysi fanlarga ko'proq e'tibor berish, kunlik reja tuzish, va online testlar orqali o'zingizni sinash.",
        'bg_color': '#8BC540',
        'icon': 'DTM',
        'img_file': 'dtm_2026_umumiy.png',
        'article_type': 'guide',
        'content': """<h2>DTM 2026 — Nima O'zgardi?</h2>

<p>DTM 2026 imtihoni O'zbekiston abituriyentlari uchun asosiy sinovdan biri bo'lib qolmoqda. Har yili minglab talabgorlar universitetga kirish uchun bu imtihondan o'tishlari zarur. Maqsadingizga erishish uchun erta tayyorlanish — g'alaba garovi.</p>

<p><strong>TestMakon.uz</strong> platformasida siz DTM 2026 ga to'liq tayyorlanishingiz mumkin — 10,000+ savol, simulyatsiya testlari va AI mentor bepul!</p>

<h2>Qaysi Fanlarni Tanlash Kerak?</h2>

<p>DTM da 3 ta fan tanlanadi: majburiy fan + 2 ta ixtiyoriy fan. Ko'pchilik abituriyentlar quyidagi kombinatsiyalarni tanlashadi:</p>

<ul>
<li><strong>Texnik yo'nalish:</strong> <a href="/tests/practice/matematika/">Matematika</a> + <a href="/tests/practice/fizika/">Fizika</a> + <a href="/tests/practice/ingliz-tili/">Ingliz tili</a></li>
<li><strong>Tibbiyot yo'nalishi:</strong> <a href="/tests/practice/biologiya/">Biologiya</a> + <a href="/tests/practice/kimyo/">Kimyo</a> + <a href="/tests/practice/ingliz-tili/">Ingliz tili</a></li>
<li><strong>Ijtimoiy yo'nalish:</strong> <a href="/tests/practice/tarix/">Tarix</a> + <a href="/tests/practice/geografiya/">Geografiya</a> + <a href="/tests/practice/ingliz-tili/">Ingliz tili</a></li>
</ul>

<h2>Kunlik Tayyorgarlik Rejasi</h2>

<p>Muvaffaqiyatli abituriyentlar tajribasiga ko'ra, <strong>kuniga 2-3 soat</strong> muntazam mashq eng yaxshi natija beradi. Quyidagi reja asosida ishlang:</p>

<ul>
<li><strong>Ertalab (30 daqiqa):</strong> Kechagi xatolarni qayta ko'rib chiqish</li>
<li><strong>Kunduzi (60 daqiqa):</strong> Yangi mavzu o'rganish + <a href="/tests/practice/">mavzu bo'yicha test</a> ishlash</li>
<li><strong>Kechqurun (30 daqiqa):</strong> <a href="/tests/quick-test/">Tezkor test</a> — 10 savol, 10 daqiqa</li>
<li><strong>Haftalik (2 soat):</strong> <a href="/tests/dtm-simulation/">DTM simulyatsiya testi</a> — to'liq imtihon sharoitida</li>
</ul>

<h2>TestMakon da DTM Tayyorgarligi</h2>

<p>TestMakon.uz platformasi DTM ga tayyorlanish uchun barcha zarur vositalarni taqdim etadi:</p>

<ul>
<li>🎯 <a href="/tests/dtm-simulation/">DTM Simulyatsiya testi</a> — 3 fan, 90 savol, 180 daqiqa</li>
<li>📚 <a href="/tests/practice/">Mavzu bo'yicha mashq</a> — har bir mavzuni alohida o'rganish</li>
<li>⚡ <a href="/tests/quick-test/">Tezkor test</a> — 10 savol, tez bilim tekshirish</li>
<li>🤖 AI Mentor — kuchsiz mavzularni aniqlash va tavsiyalar</li>
<li>📊 Batafsil tahlil — xato qilgan savollar, statistika</li>
</ul>

<h2>Ball Hisoblash</h2>

<p>DTM da har bir to'g'ri javob uchun ball beriladi. Har bir fan bo'yicha maksimal 33.3 ball, jami 99.9 ball. Grant olish uchun odatda 56-70+ ball kerak bo'ladi (yo'nalishga qarab farq qiladi).</p>

<p><strong>Hoziroq boshlang:</strong> <a href="/tests/dtm-simulation/">DTM Simulyatsiya Test →</a></p>""",
    },
    {
        'slug': 'dtm-2026-matematika-formulalar-va-mavzular',
        'title': "DTM 2026 Matematika: Muhim Formulalar va Mavzular",
        'meta_title': "DTM 2026 Matematika — Formulalar va Mavzular | TestMakon.uz",
        'meta_description': "DTM 2026 matematika imtihoni uchun eng muhim formulalar, mavzular va maslahatlar. Algebra, geometriya, trigonometriya. Online mashq testlari bepul!",
        'excerpt': "DTM 2026 matematika bo'limida eng ko'p chiqadigan mavzular: algebra, geometriya, trigonometriya, logarifmlar. Formulalar va online testlar.",
        'bg_color': '#3B82F6',
        'icon': 'MAT',
        'img_file': 'dtm_2026_matematika.png',
        'article_type': 'guide',
        'content': """<h2>DTM 2026 Matematika — Nechta Savol?</h2>

<p>DTM imtihonida matematikadan <strong>30 ta savol</strong> beriladi. Har bir to'g'ri javob uchun <strong>1.1 ball</strong> beriladi. Maksimal ball — 33.3. Ko'pchilik abituriyentlar uchun matematika eng muhim fan hisoblanadi.</p>

<h2>Eng Ko'p Chiqadigan Mavzular</h2>

<p>Statistikaga ko'ra, DTM matematika savollarining katta qismi quyidagi mavzulardan tuziladi:</p>

<ul>
<li><strong>Algebra (35%):</strong> Tenglamalar, tengsizliklar, progressiyalar, logarifmlar, ko'rsatkichli funksiyalar</li>
<li><strong>Geometriya (30%):</strong> Uchburchaklar, to'rtburchaklar, aylana, fazoviy geometriya</li>
<li><strong>Trigonometriya (20%):</strong> Sin, cos, tan, formulalar, tenglamalar</li>
<li><strong>Analiz (15%):</strong> Hosilalar, integrallar, funksiyalar</li>
</ul>

<h2>Muhim Formulalar</h2>

<p><strong>Kvadrat tenglamaning ildizlari:</strong><br>
x = (−b ± √(b²−4ac)) / 2a</p>

<p><strong>Trigonometriya asosiy formulalari:</strong><br>
sin²x + cos²x = 1<br>
sin(a+b) = sin·a·cos·b + cos·a·sin·b<br>
cos(a+b) = cos·a·cos·b − sin·a·sin·b</p>

<p><strong>Progressiyalar:</strong><br>
Arifmetik progressiya n-hadi: an = a1 + (n−1)·d<br>
Geometrik progressiya n-hadi: bn = b1·q^(n−1)</p>

<h2>Tayyorgarlik Tavsiyalari</h2>

<ol>
<li>Har kuni <a href="/tests/practice/matematika/">matematika bo'yicha mavzu testlarini</a> ishlang</li>
<li>Xato qilgan masalalarni daftarga yozing va qaytaring</li>
<li>DTM formulalarini har kuni qaytaring</li>
<li>Haftalik <a href="/tests/dtm-simulation/">simulyatsiya test</a> orqali o'zingizni tekshiring</li>
</ol>

<p><strong>Matematika testlarini boshlash:</strong> <a href="/tests/practice/matematika/">Matematika Mashq Testlari →</a></p>""",
    },
    {
        'slug': 'dtm-2026-fizika-qonunlar-va-formulalar',
        'title': "DTM 2026 Fizika: Asosiy Qonunlar va Formulalar",
        'meta_title': "DTM 2026 Fizika Formulalar va Mavzular | TestMakon.uz",
        'meta_description': "DTM 2026 fizika imtihoni uchun asosiy qonunlar, formulalar va mavzular. Mexanika, termodinamika, optika, elektr. TestMakon da bepul online testlar!",
        'excerpt': "DTM 2026 fizika bo'limida eng muhim mavzular: mexanika, termodinamika, elektrodinamika, optika. Formulalar jadvali va online mashq testlari.",
        'bg_color': '#8B5CF6',
        'icon': 'FIZ',
        'img_file': 'dtm_2026_fizika.png',
        'article_type': 'guide',
        'content': """<h2>DTM 2026 Fizika — Umumiy Ma'lumot</h2>

<p>DTM imtihonida fizikadan <strong>30 ta savol</strong> beriladi. Fizika ko'pchilik abituriyentlar uchun qiyin fan bo'lib, lekin to'g'ri tayyorgarlik bilan yuqori ball olish mumkin.</p>

<h2>Asosiy Mavzular va Ulushlar</h2>

<ul>
<li><strong>Mexanika (40%):</strong> Kinematika, dinamika, statika, energiya, impuls</li>
<li><strong>Termodinamika (20%):</strong> Gaz qonunlari, issiqliq miqdori, entropiya</li>
<li><strong>Elektrodinamika (25%):</strong> Elektr maydon, tok, magnit maydon</li>
<li><strong>Optika va atom fizikasi (15%):</strong> Yorug'lik, fotonlar, yadro fizikasi</li>
</ul>

<h2>Muhim Formulalar</h2>

<p><strong>Mexanika:</strong><br>
F = ma (Nyuton II qonuni)<br>
E_k = mv²/2 (kinetik energiya)<br>
E_p = mgh (potensial energiya)<br>
p = mv (impuls)</p>

<p><strong>Termodinamika:</strong><br>
pV = νRT (ideal gaz holat tenglamasi)<br>
Q = cm·ΔT (issiqliq miqdori)</p>

<p><strong>Elektr:</strong><br>
F = kq₁q₂/r² (Kulon qonuni)<br>
U = IR (Om qonuni)<br>
P = UI (elektr quvvat)</p>

<h2>Tayyorgarlik Strategiyasi</h2>

<ol>
<li>Formulalar jadvalini yarating va har kuni ko'rib chiqing</li>
<li>Har bir mavzu bo'yicha <a href="/tests/practice/fizika/">fizika testlarini</a> ishlang</li>
<li>Masalalar yechishni ko'p mashq qiling — ayniqsa mexanika</li>
<li>Haftalik <a href="/tests/block-test/">blok test</a> orqali o'zingizni baholang</li>
</ol>

<p><strong>Fizika testlarini boshlash:</strong> <a href="/tests/practice/fizika/">Fizika Mashq Testlari →</a></p>""",
    },
    {
        'slug': 'dtm-2026-biologiya-eng-kop-chiqadigan-mavzular',
        'title': "DTM 2026 Biologiya: Eng Ko'p Chiqadigan Mavzular",
        'meta_title': "DTM 2026 Biologiya Mavzular va Testlar | TestMakon.uz",
        'meta_description': "DTM 2026 biologiya imtihonida eng ko'p chiqadigan mavzular: hujayra biologiyasi, genetika, ekologiya. Bepul online biologiya testlari TestMakon da!",
        'excerpt': "DTM 2026 biologiya bo'limida eng muhim mavzular: hujayra biologiyasi, genetika, evolyutsiya, ekologiya. Online mashq testlari va tavsiyalar.",
        'bg_color': '#10B981',
        'icon': 'BIO',
        'img_file': 'dtm_2026_biologiya.png',
        'article_type': 'guide',
        'content': """<h2>DTM 2026 Biologiya — Nima O'rganish Kerak?</h2>

<p>Biologiya tibbiyot, veterinariya va qishloq xo'jaligi yo'nalishlariga kiruvchi abituriyentlar uchun asosiy fanlardan biridir. DTM da biologiyadan <strong>30 ta savol</strong> beriladi.</p>

<h2>Eng Ko'p Chiqadigan Mavzular</h2>

<ul>
<li><strong>Hujayra biologiyasi (25%):</strong> Hujayra tuzilishi, organoidlar, mitoz va meyoz, DNK replikatsiyasi</li>
<li><strong>Genetika (30%):</strong> Mendel qonunlari, belgilar irsiyati, mutatsiyalar, seleksiya</li>
<li><strong>Evolyutsiya (15%):</strong> Darvin nazariyasi, tabiiy tanlanish, populyatsiya genetikasi</li>
<li><strong>Ekologiya (20%):</strong> Ekotizimlar, oziqlanish zanjiri, biotsenoz</li>
<li><strong>Odam anatomiyasi (10%):</strong> Organlar sistemalari, fiziologiya</li>
</ul>

<h2>Genetika — Eng Muhim Bo'lim</h2>

<p>Statistikaga ko'ra, DTM biologiya savollarining 30% genetikadan tashkil topadi. Quyidagilarni yaxshi o'rganing:</p>

<ul>
<li>Mendel qonunlari (dominant va retsessiv belgilar)</li>
<li>Qo'shilgan irsiyat va jinsga bog'liq irsiyat</li>
<li>Mutatsiyalar turlari</li>
<li>Genotip va fenotip farqi</li>
</ul>

<h2>Samarali Tayyorgarlik Usullari</h2>

<ol>
<li><a href="/tests/practice/biologiya/">Biologiya mavzu testlarini</a> muntazam ishlang</li>
<li>Hujayra organoidlari va ularning vazifalarini yodlang</li>
<li>Genetika masalalarini ko'p ishlang</li>
<li>Terminologiyaga alohida e'tibor bering</li>
</ol>

<p><strong>Biologiya testlarini boshlash:</strong> <a href="/tests/practice/biologiya/">Biologiya Mashq Testlari →</a></p>""",
    },
    {
        'slug': 'dtm-2026-kimyo-formulalar-va-reaksiyalar',
        'title': "DTM 2026 Kimyo: Formulalar va Reaksiyalar Tahlili",
        'meta_title': "DTM 2026 Kimyo Formulalar va Testlar | TestMakon.uz",
        'meta_description': "DTM 2026 kimyo imtihoni uchun muhim formulalar, kimyoviy reaksiyalar va maslahatlar. Organik va noorganik kimyo. Bepul online testlar TestMakon da!",
        'excerpt': "DTM 2026 kimyo bo'limida eng muhim mavzular: noorganik va organik kimyo, reaksiyalar, eritmalar. Formulalar va online mashq testlari.",
        'bg_color': '#F59E0B',
        'icon': 'KIM',
        'img_file': 'dtm_2026_kimyo.png',
        'article_type': 'guide',
        'content': """<h2>DTM 2026 Kimyo — Asosiy Ma'lumot</h2>

<p>Kimyo fani tibbiyot, farmatsevtika va kimyo muhandisligi yo'nalishlari uchun talab qilinadigan fandir. DTM da kimyodan <strong>30 ta savol</strong> beriladi.</p>

<h2>Kimyo Bo'limlari va Ulushlar</h2>

<ul>
<li><strong>Noorganik kimyo (40%):</strong> Elementlar, oksidlar, kislotalar, asoslar, tuzlar, elektroliz</li>
<li><strong>Organik kimyo (35%):</strong> Uglevodorodlar, spirtlar, kislotalar, aminlar, oqsillar</li>
<li><strong>Umumiy kimyo (25%):</strong> Atom tuzilishi, kimyoviy bog'lanish, eritmalar, pH</li>
</ul>

<h2>Muhim Reaksiyalar va Formulalar</h2>

<p><strong>Kislota + Asos → Tuz + Suv:</strong><br>
HCl + NaOH → NaCl + H₂O</p>

<p><strong>Metall + Kislota:</strong><br>
Zn + 2HCl → ZnCl₂ + H₂↑</p>

<p><strong>Molyar massa:</strong><br>
M = m/n (g/mol)</p>

<p><strong>pH hisoblash:</strong><br>
pH = −lg[H⁺]</p>

<h2>Organik Kimyo — Eng Qiyin Bo'lim</h2>

<p>Ko'pchilik abituriyentlar organik kimyoni qiyin deb hisoblashadi. Quyidagilarga e'tibor bering:</p>

<ul>
<li>Uglevodorodlar: alkanlar, alkenlar, alkinlar, arenlar</li>
<li>Kislorodli birikmalar: spirtlar, aldegidlar, ketonlar, kislotalar</li>
<li>Azotli birikmalar: aminlar, aminokislotalar, oqsillar</li>
</ul>

<h2>Tayyorgarlik Bo'yicha Maslahatlar</h2>

<ol>
<li>Elementlar davriy jadvalini yaxshi o'zlashtiring</li>
<li>Kimyoviy reaksiyalar tenglamasini balanslashni mashq qiling</li>
<li><a href="/tests/practice/kimyo/">Kimyo mavzu testlarini</a> ko'p ishlang</li>
<li>Masala yechish algoritmlarini o'rganing</li>
</ol>

<p><strong>Kimyo testlarini boshlash:</strong> <a href="/tests/practice/kimyo/">Kimyo Mashq Testlari →</a></p>""",
    },
    {
        'slug': 'dtm-2026-ball-hisoblash-grant-va-kontrakt',
        'title': "DTM 2026 Ball Hisoblash: Grant va Kontrakt Ballari",
        'meta_title': "DTM 2026 Ball Hisoblash — Grant va Kontrakt | TestMakon.uz",
        'meta_description': "DTM 2026 da ball qanday hisoblanadi? Grant olish uchun necha ball kerak? Universitetlar bo'yicha grant ballari va kontrakt narxlari. TestMakon.uz",
        'excerpt': "DTM 2026 da ball hisoblash tizimi, grant olish uchun kerakli ball, universitetlar bo'yicha o'tish ballari va kontrakt narxlari.",
        'bg_color': '#EF4444',
        'icon': 'DTM',
        'img_file': 'dtm_2026_ball.png',
        'article_type': 'guide',
        'content': """<h2>DTM 2026 Ball Hisoblash Tizimi</h2>

<p>DTM imtihonida jami <strong>99.9 ball</strong> to'planishi mumkin. Har bir fandan maksimal 33.3 ball beriladi. To'g'ri javob uchun ball, noto'g'ri javob uchun hech qanday jazo yo'q — shuning uchun barcha savollarga javob bering!</p>

<h2>Ball Hisoblash Formulasi</h2>

<p>Har bir fan uchun ball = (To'g'ri javoblar soni / 30) × 33.3</p>

<p><strong>Misol:</strong> Matematikadan 24 ta to'g'ri javob bersangiz:<br>
Ball = (24 / 30) × 33.3 = 26.64 ball</p>

<h2>Grant va Kontrakt Ballari</h2>

<p>Grant olish uchun kerakli ball universitetga va yo'nalishga qarab farq qiladi:</p>

<ul>
<li><strong>Top universitetlar (ToshDTU, NUUz, ToshTIMI):</strong> 70-85+ ball</li>
<li><strong>O'rta universitetlar:</strong> 56-70 ball</li>
<li><strong>Regional universitetlar:</strong> 45-60 ball</li>
</ul>

<p>Aniq balllarni <a href="/universities/">Universitetlar sahifasida</a> ko'rishingiz mumkin.</p>

<h2>Kontrakt Narxlari</h2>

<p>Grant olmagan abituriyentlar kontrakt asosida o'qish imkoniyatiga ega. Kontrakt narxlari yo'nalishga qarab farq qiladi va har yili o'zgarib turadi. Eng so'nggi ma'lumotlar uchun universitetlarning rasmiy saytlarini tekshiring.</p>

<h2>Qanday Yuqori Ball Olish Mumkin?</h2>

<ol>
<li><strong>Muntazam mashq:</strong> <a href="/tests/practice/">Mavzu bo'yicha testlarni</a> har kuni ishlang</li>
<li><strong>Simulyatsiya:</strong> <a href="/tests/dtm-simulation/">DTM simulyatsiya testini</a> haftalik ishlang</li>
<li><strong>Xatolarni tahlil qilish:</strong> AI mentor bilan kuchsiz mavzularingizni aniqlang</li>
<li><strong>Vaqtni boshqarish:</strong> 180 daqiqada 90 savolni ulgurishni mashq qiling</li>
</ol>

<p><strong>Hoziroq simulyatsiya testni boshlang:</strong> <a href="/tests/dtm-simulation/">DTM Simulyatsiya Test →</a></p>

<p>Universitetlar va o'tish ballari haqida batafsil: <a href="/universities/">Universitetlar sahifasi →</a></p>""",
    },
]


# ─── Migration funksiyalari ───────────────────────────────────────────────────

def create_dtm_articles(apps, schema_editor):
    from django.conf import settings

    Category = apps.get_model('news', 'Category')
    Article = apps.get_model('news', 'Article')

    # Kategoriya
    category, _ = Category.objects.get_or_create(
        slug='dtm-2026',
        defaults={
            'name': 'DTM 2026',
            'icon': '🎯',
            'color': '#8BC540',
            'is_active': True,
            'order': 1,
        }
    )

    media_root = str(settings.MEDIA_ROOT)
    img_dir = os.path.join(media_root, 'news', 'images')
    os.makedirs(img_dir, exist_ok=True)

    now = timezone.now()

    for i, data in enumerate(ARTICLES):
        if Article.objects.filter(slug=data['slug']).exists():
            continue

        img_path = os.path.join(img_dir, data['img_file'])
        img_created = _create_cover_image(
            filepath=img_path,
            bg_color_hex=data['bg_color'],
            title_line1=data['title'].split(':')[0] if ':' in data['title'] else data['title'][:30],
            title_line2=data['title'].split(':')[1].strip() if ':' in data['title'] else '',
            icon_text=data['icon'],
        )

        article = Article(
            slug=data['slug'],
            title=data['title'],
            excerpt=data['excerpt'],
            content=data['content'],
            article_type=data['article_type'],
            category=category,
            meta_title=data['meta_title'],
            meta_description=data['meta_description'],
            is_published=True,
            is_featured=(i < 2),
            is_pinned=(i == 0),
            published_at=now - timezone.timedelta(hours=i),
        )

        if img_created and os.path.exists(img_path):
            article.featured_image = f'news/images/{data["img_file"]}'

        article.save()
        print(f"  ✅ Maqola yaratildi: {data['title'][:50]}")


def delete_dtm_articles(apps, schema_editor):
    Article = apps.get_model('news', 'Article')
    Category = apps.get_model('news', 'Category')
    for data in ARTICLES:
        Article.objects.filter(slug=data['slug']).delete()
    Category.objects.filter(slug='dtm-2026').delete()


class Migration(migrations.Migration):

    dependencies = [
        ('news', '0002_systembanner'),
    ]

    operations = [
        migrations.RunPython(create_dtm_articles, delete_dtm_articles),
    ]
