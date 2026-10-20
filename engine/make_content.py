"""Render Payhip gallery images, Pinterest pins, and vertical videos from real workbook screenshots."""
import os, subprocess, csv, json
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT = os.path.dirname(os.path.abspath(__file__))
SH = os.path.join(ROOT, "shots")
OUT = os.path.join(ROOT, "content")
for d in ("gallery", "pins", "videos", "_tmp"):
    os.makedirs(os.path.join(OUT, d), exist_ok=True)

NAVY, NAVY2, GREEN, CREAM, WHITE = (31, 78, 121), (18, 49, 79), (46, 139, 87), (255, 246, 213), (255, 255, 255)
PB = "/usr/share/fonts/truetype/google-fonts/Poppins-Bold.ttf"
PS = "/usr/share/fonts/truetype/google-fonts/Poppins-SemiBold.ttf"
PR = "/usr/share/fonts/truetype/google-fonts/Poppins-Regular.ttf"
for p in (PS, PR):
    if not os.path.exists(p):
        globals()[[k for k, v in globals().items() if v == p][0]] = PB


def font(path, size):
    return ImageFont.truetype(path, size)


def shot(name):
    return Image.open(os.path.join(SH, f"shot_{name}.png")).convert("RGB")


def shot_tall(name):
    """Wide tables -> two stacked halves, each keeping the label column, so they read on a phone."""
    import numpy as np
    im = shot(name)

    def navy_of(img):
        a = np.asarray(img).astype(int)
        return (abs(a[:, :, 0] - 31) < 12) & (abs(a[:, :, 1] - 78) < 12) & (abs(a[:, :, 2] - 121) < 12)

    navy = navy_of(im)
    yh = int(navy.sum(axis=1).argmax())
    row = navy[yh]
    xs = np.where(row)[0]
    x_start = xs[0]
    x_end = x_start
    for x in xs:  # first contiguous header run = main table (drops side summaries)
        if x - x_end > 25:
            break
        x_end = x
    if name != "dashboard":
        im = im.crop((0, 0, min(x_end + 40, im.width), im.height))
        navy = navy_of(im)
        row = navy[yh]
    if im.width / im.height < 2.0:
        return im
    seps = [x for x in range(x_start + 5, x_end - 5) if not row[x] and row[x - 1]]
    first = seps[0]
    mid = x_start + (x_end - x_start) / 2
    split = min(seps[1:], key=lambda x: abs(x - mid))
    col = navy[:, int(mid)]
    ys = np.where(col)[0]
    hdr = int(ys[0]) - 4  # top of the header band
    top = im.crop((0, 0, split, im.height))
    rest = im.crop((split, 0, x_end + 3, im.height))
    lab = im.crop((x_start, 0, first, im.height))
    bottom = Image.new("RGB", (lab.width + rest.width, im.height - hdr), "white")
    bottom.paste(lab.crop((0, hdr, lab.width, lab.height)), (0, 0))
    bottom.paste(rest.crop((0, hdr, rest.width, rest.height)), (lab.width, 0))
    W = max(top.width, x_start + bottom.width)
    out = Image.new("RGB", (W, top.height + bottom.height + 30), "white")
    out.paste(top, (0, 0))
    out.paste(bottom, (x_start, top.height + 30))
    return out


def bg(w, h):
    im = Image.new("RGB", (w, h), NAVY)
    d = ImageDraw.Draw(im)
    for y in range(h):  # vertical gradient
        t = y / h
        c = tuple(int(NAVY[i] * (1 - t) + NAVY2[i] * t) for i in range(3))
        d.line([(0, y), (w, y)], fill=c)
    return im


def wrap(draw, text, fnt, maxw):
    words, lines, cur = text.split(), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if draw.textlength(t, font=fnt) <= maxw:
            cur = t
        else:
            lines.append(cur)
            cur = w
    lines.append(cur)
    return lines


def text_block(draw, text, fnt, x, y, maxw, fill=WHITE, center=False, w=None, gap=1.15, hl=None):
    lines = wrap(draw, text, fnt, maxw)
    lh = int(fnt.size * gap)
    for ln in lines:
        tx = x + (w - draw.textlength(ln, font=fnt)) / 2 if center else x
        if hl:  # highlight bar behind text
            tw = draw.textlength(ln, font=fnt)
            draw.rounded_rectangle([tx - 18, y + 6, tx + tw + 18, y + lh + 2], radius=14, fill=hl)
        draw.text((tx, y), ln, font=fnt, fill=fill)
        y += lh + (10 if hl else 0)
    return y


def card(img, maxw, maxh, radius=22):
    s = min(maxw / img.width, maxh / img.height)
    im = img.resize((int(img.width * s), int(img.height * s)), Image.LANCZOS)
    pad = 18
    maxw -= 116
    s2 = min(maxw / img.width, maxh / img.height)
    im = img.resize((int(img.width * s2), int(img.height * s2)), Image.LANCZOS)
    c = Image.new("RGBA", (im.width + pad * 2, im.height + pad * 2), (0, 0, 0, 0))
    m = Image.new("L", c.size, 0)
    ImageDraw.Draw(m).rounded_rectangle([0, 0, c.width - 1, c.height - 1], radius=radius, fill=255)
    base = Image.new("RGBA", c.size, (255, 255, 255, 255))
    base.paste(im, (pad, pad))
    c.paste(base, (0, 0), m)
    sh = Image.new("RGBA", (c.width + 80, c.height + 80), (0, 0, 0, 0))
    sm = Image.new("L", sh.size, 0)
    ImageDraw.Draw(sm).rounded_rectangle([40, 52, 40 + c.width, 52 + c.height], radius=radius, fill=110)
    sm = sm.filter(ImageFilter.GaussianBlur(22))
    sh.putalpha(sm)
    sh.paste(c, (40, 40), c)
    return sh


def brand(draw, w, y, size=30, color=(200, 216, 232)):
    f = font(PS, size)
    t = "CAMPUS DIGITAL CO."
    draw.text(((w - draw.textlength(t, font=f)) / 2, y), t, font=f, fill=color)


def pill(draw, text, cx, y, size=40, fill=GREEN, color=WHITE):
    f = font(PB, size)
    tw = draw.textlength(text, font=f)
    draw.rounded_rectangle([cx - tw / 2 - 40, y, cx + tw / 2 + 40, y + size * 1.9], radius=size, fill=fill)
    draw.text((cx - tw / 2, y + size * 0.42), text, font=f, fill=color)


# ---------------- PAYHIP GALLERY (1600x1200) ----------------
GALLERY = [
    ("01_cover", "dashboard", "College Money Toolkit", "Budget · Expenses · Savings · Loans · Semester — all in one spreadsheet"),
    ("02_dashboard", "dashboard", "Your whole month at a glance", "Income, spending, savings rate and charts update automatically"),
    ("03_budget", "budget", "A budget that fills itself in", "Log a purchase once — Actual, Remaining and % used update for you"),
    ("04_loans", "loans", "See your loan payoff date", "Total interest, payoff month, and what an extra $25/mo saves"),
    ("05_savings", "savings", "Hit every savings goal", "Progress bars + exactly how much to save per month"),
    ("06_semester", "semester", "No surprise semester costs", "Tuition, books, fees and trips — and what to set aside monthly"),
    ("07_expenses", "expenses", "Track every dollar in seconds", "Dropdown categories, monthly totals, works in Excel & Google Sheets"),
]
for fn, sname, h, sub in GALLERY:
    W, H = 1600, 1200
    im = bg(W, H)
    d = ImageDraw.Draw(im)
    big = fn == "01_cover"
    y = text_block(d, h, font(PB, 78 if big else 64), 80, 60, W - 160, center=True, w=W - 160)
    y = text_block(d, sub, font(PR, 34), 80, y + 6, W - 160, fill=(200, 216, 232), center=True, w=W - 160)
    c = card(shot(sname), W - 200, H - y - (190 if big else 90))
    im.paste(c, ((W - c.width) // 2, y + 10), c)
    if big:
        pill(d, "Excel + Google Sheets  ·  Instant download", W // 2, H - 110, size=32)
    im.save(os.path.join(OUT, "gallery", f"{fn}.png"), optimize=True)

# ---------------- PINTEREST PINS (1000x1500) ----------------
PINS = [
    ("college-budget-spreadsheet", "dashboard", "College Budget Spreadsheet", "that does the math for you",
     "College Budget Spreadsheet Template (Excel + Google Sheets)"),
    ("student-budget-template", "budget", "Student Budget Template", "set targets · log spending · done",
     "Monthly Budget Template for College Students"),
    ("student-loan-payoff-tracker", "loans", "Student Loan Payoff Tracker", "see your payoff date + interest saved",
     "Student Loan Payoff Calculator Spreadsheet"),
    ("college-savings-goal-tracker", "savings", "Savings Goal Tracker", "spring break · emergency fund · laptop",
     "Savings Goal Tracker Spreadsheet for Students"),
    ("semester-expense-planner", "semester", "Semester Expense Planner", "plan tuition, books & fees early",
     "College Semester Cost Planner Template"),
    ("college-expense-tracker", "expenses", "College Expense Tracker", "every dollar, one dropdown",
     "Expense Tracker Spreadsheet for College Students"),
    ("bill-tracker-college", "bills", "Bill Tracker for Students", "never miss rent again",
     "Monthly Bill Tracker Template (Paid / Unpaid)"),
    ("money-dashboard-students", "dashboard", "Money Dashboard", "for college students",
     "Personal Finance Dashboard Spreadsheet for Students"),
    ("budget-vs-actual", "budget", "Budget vs. Actual", "see where you overspent instantly",
     "Budget vs Actual Spreadsheet Template"),
    ("extra-loan-payment", "loans", "$25/mo extra on a loan", "can save $800+ in interest",
     "Extra Student Loan Payment Calculator"),
    ("spring-break-fund", "savings", "Spring Break Fund", "how much to save each month",
     "Spring Break Savings Planner Spreadsheet"),
    ("textbook-costs", "semester", "Hidden College Costs", "budget for them before they hit",
     "College Cost Checklist + Planner Spreadsheet"),
    ("dorm-budget", "budget", "Dorm Life Budget", "simple monthly budget for students",
     "Simple Monthly Budget Spreadsheet for Dorm Students"),
    ("first-apartment-budget", "bills", "First Apartment Budget", "rent, utilities & bills in one place",
     "First Apartment Bill + Budget Tracker"),
    ("college-money-toolkit", "dashboard", "College Money Toolkit", "6 money tools · one spreadsheet",
     "All-in-One College Finance Spreadsheet Toolkit"),
]
for slug, sname, h1, h2, _ in PINS:
    W, H = 1000, 1500
    im = bg(W, H)
    d = ImageDraw.Draw(im)
    brand(d, W, 50, 26)
    y = text_block(d, h1, font(PB, 74), 60, 110, W - 120, center=True, w=W - 120, gap=1.08)
    y = text_block(d, h2, font(PS, 40), 60, y + 10, W - 120, fill=(244, 214, 120), center=True, w=W - 120)
    c = card(shot_tall(sname), W - 30, H - y - 250)
    im.paste(c, ((W - c.width) // 2, y + 20), c)
    pill(d, "Excel + Google Sheets", W // 2, H - 175, size=36)
    im.save(os.path.join(OUT, "pins", f"pin_{slug}.png"), optimize=True)

# ---------------- VIDEOS (1080x1920, ~12s, H.264) ----------------
VIDEOS = [
    ("v01_where_money_goes", "dashboard", "POV: you finally know where your money goes every month"),
    ("v02_budget_fills_itself", "budget", "a college budget that literally fills itself in"),
    ("v03_extra_25_loan", "loans", "$25 extra a month on a $5,500 student loan saves ~$800 in interest"),
    ("v04_spring_break", "savings", "how much to save every month to afford spring break"),
    ("v05_hidden_costs", "semester", "semester costs nobody warns you about until they hit"),
    ("v06_bills", "bills", "how to never forget a bill in college again"),
    ("v07_track_every_dollar", "expenses", "what tracking every dollar for a month looks like"),
    ("v08_replaced_apps", "dashboard", "the $5 spreadsheet that replaced 3 budgeting apps"),
    ("v09_over_budget", "budget", "red = over budget. now you know exactly what to cut"),
    ("v10_loan_interest", "loans", "your student loans cost way more than the balance says"),
]
FPS, MAIN, END = 30, 9.5, 3.0


def frame_main(sname, hook):
    W, H = 1080, 1920
    im = bg(W, H)
    d = ImageDraw.Draw(im)
    brand(d, W, 150, 28)
    y = text_block(d, hook, font(PB, 66), 70, 230, W - 140, fill=NAVY2, center=True, w=W - 140, hl=WHITE, gap=1.12)
    c = card(shot_tall(sname), W - 10, H - y - 420)
    im.paste(c, ((W - c.width) // 2, y + 40), c)
    return im


def frame_end():
    W, H = 1080, 1920
    im = bg(W, H)
    d = ImageDraw.Draw(im)
    c = card(shot("dashboard"), W - 140, 620)
    im.paste(c, ((W - c.width) // 2, 560), c)
    y = text_block(d, "College Money Toolkit", font(PB, 78), 60, 300, W - 120, center=True, w=W - 120)
    text_block(d, "Budget · Expenses · Bills · Savings · Loans · Semester", font(PR, 34), 60, 1260, W - 120,
               fill=(200, 216, 232), center=True, w=W - 120)
    pill(d, "Link in bio  ·  $4.99", W // 2, 1400, size=52)
    brand(d, W, 1640, 30)
    return im


endp = os.path.join(OUT, "_tmp", "end.png")
frame_end().save(endp)
for slug, sname, hook in VIDEOS:
    mp = os.path.join(OUT, "_tmp", f"{slug}.png")
    frame_main(sname, hook).save(mp)
    out = os.path.join(OUT, "videos", f"{slug}.mp4")
    n1, n2 = int(MAIN * FPS), int(END * FPS)
    flt = (
        f"[0:v]scale=2160:3840,zoompan=z='min(1+0.0009*on,1.09)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={n1}:s=1080x1920:fps={FPS},"
        f"fade=t=in:st=0:d=0.3,setsar=1[a];"
        f"[1:v]scale=1080:1920,zoompan=z='1':d={n2}:s=1080x1920:fps={FPS},setsar=1[b];"
        f"[a][b]xfade=transition=slideup:duration=0.5:offset={MAIN-0.5},format=yuv420p[v]"
    )
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-loop", "1", "-t", str(MAIN), "-i", mp,
                    "-loop", "1", "-t", str(END), "-i", endp,
                    "-f", "lavfi", "-t", str(MAIN + END - 0.5), "-i", "anullsrc=r=44100:cl=stereo",
                    "-filter_complex", flt, "-map", "[v]", "-map", "2:a", "-c:v", "libx264", "-preset", "medium",
                    "-crf", "20", "-r", str(FPS), "-c:a", "aac", "-shortest", "-movflags", "+faststart", out], check=True)
    print("video", slug)

json.dump({"pins": PINS, "videos": VIDEOS}, open(os.path.join(OUT, "_tmp", "manifest.json"), "w"))
print("done")
