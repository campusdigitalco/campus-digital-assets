# Weekly content refill — Campus Digital Co.

Store: https://payhip.com/b/Mm2Uu · Metricool brand (blogId) 7510880 · timezone America/New_York
Pinterest boards: "College Budget & Money Tips", "Student Spreadsheet Templates"

## Steps
1. Clone this repo (`git clone --depth 1 https://github.com/campusdigitalco/campus-digital-assets`).
2. Metricool: getBrandSettings → see which networks are connected (instagram, pinterest, tiktok, youtube).
3. Pull last 7 days of analytics per connected network (getAnalyticsAvailableMetrics → getAnalyticsDataByMetrics).
   Rank last week's posts by link clicks/saves (Pinterest) and views/shares (Reels/TikTok/Shorts). Note which sheet (dashboard, budget, loans, savings, semester, bills, expenses) and which hook style won.
4. Write NEW content for next week, weighted ~60% toward the winning sheets/hook styles:
   - 10 video hooks (short, lowercase-casual, specific numbers only if they come from the demo workbook)
   - 15 pin specs (headline, subline, SEO title)
   Never repeat a hook used in a prior week (check prior w*/ folders and the scheduled posts).
5. In engine/make_content.py replace the GALLERY-free lists `PINS` and `VIDEOS` with the new ones, set OUT to a new folder `w{N}` (next week number), and run `python3 make_content.py` from engine/ (needs ffmpeg, Pillow, Poppins font; install fonts-poppins or fall back to DejaVu if missing).
   Visually check 2 pins + 2 video frames before publishing.
6. Copy outputs to `w{N}/pins` and `w{N}/videos`, commit, push to main.
7. Schedule via Metricool createScheduledPost with media URLs
   `https://raw.githubusercontent.com/campusdigitalco/campus-digital-assets/main/w{N}/...`:
   - Pinterest: 3/day at 09:00, 15:00, 21:00, alternate boards, pinLink = store URL
   - Instagram: REEL 2/day at 12:30, 19:30
   - TikTok (if connected): same videos 2/day at 12:30, 19:30, tiktokData title = hook
   - YouTube (if connected): type "short", madeForKids false, title = hook (≤95 chars)
   Captions end with "Full College Money Toolkit at the link in bio." + hashtags.
8. Report: 5 lines — last week's best/worst post, totals, what changed this week, anything broken (disconnected network, failed posts).
