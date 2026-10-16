"""AI Math Tutor — interactive geometry learning for grades 5–9.
Run with: python -m streamlit run app.py
"""
import math
import html
import json
import os
import time
import random
import re
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode
import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="AI Math Tutor", page_icon="📐", layout="wide", initial_sidebar_state="auto")

if "page" not in st.session_state:
    st.session_state.page = "Home"
if "shape" not in st.session_state:
    st.session_state.shape = None
if "task" not in st.session_state:
    st.session_state.task = None
if "level" not in st.session_state:
    st.session_state.level = {"Practice": "Basic", "AI Generator": "Basic"}

COLORS = {"Home": "#334155", "Formulas": "#2563eb", "Practice": "#16a34a", "AI Generator": "#dc2626"}
page = st.session_state.page
accent = COLORS[page]
dark = False  # Fixed light theme for consistent colors


def navigate(destination):
    st.session_state.page = destination
    st.session_state.shape = None
    st.session_state.task = None
    st.rerun()


def difficulty(section):
    st.markdown("**Choose your difficulty level**")
    cols = st.columns(3)
    for col, name in zip(cols, ("Basic", "Standard", "Advanced")):
        with col:
            selected = st.session_state.level[section] == name
            if st.button(("✓ " if selected else "") + name, key=f"level_{section}_{name}",
                         type="primary" if selected else "secondary", use_container_width=True):
                if not selected:
                    st.session_state.level[section] = name
                    if section == "Practice":
                        st.session_state.task = None
                    st.rerun()
    return st.session_state.level[section]


# A consistent, lightly illustrated math-notebook background.
# The SVG is a background image (not inline HTML), so it cannot hide text or buttons.
notebook_art = """<svg xmlns="http://www.w3.org/2000/svg" width="850" height="690" viewBox="0 0 850 690">
<g fill="none" stroke-width="2.2" stroke-linejoin="round" opacity=".35">
<path d="M78 110 L150 110 L114 48 Z" stroke="#2563eb"/>
<rect x="680" y="75" width="75" height="52" rx="2" stroke="#16a34a" transform="rotate(12 718 101)"/>
<circle cx="426" cy="130" r="38" stroke="#dc2626"/>
<path d="M398 130 H454 M426 92 V168" stroke="#dc2626" stroke-dasharray="4 6" stroke-width="1.5"/>
<path d="M75 415 H170 V480 H75 Z M75 415 L170 480" stroke="#0ea5e9"/>
<path d="M630 405 H730 L690 480 H665 Z" stroke="#8b5cf6"/>
<path d="M300 560 L335 500 L370 560 Z" stroke="#16a34a"/>
<path d="M335 500 V560" stroke="#16a34a" stroke-dasharray="4 5" stroke-width="1.5"/>
<path d="M495 605 L555 605 M525 575 L525 635" stroke="#2563eb" stroke-width="2"/>
</g>
<g fill="#64748b" opacity=".33" font-family="Arial,sans-serif" font-size="20">
<text x="220" y="265" transform="rotate(-12 220 265)">a² + b² = c²</text>
<text x="540" y="285" transform="rotate(9 540 285)">πr²</text>
<text x="135" y="625" transform="rotate(-8 135 625)">∠ 90°</text>
<text x="745" y="600" transform="rotate(12 745 600)">P = 2(a+b)</text>
</g></svg>"""
notebook_url = 'data:image/svg+xml,' + quote(notebook_art, safe='')

st.markdown(f"""
<style>
.stApp {{background-color:#f8fafc;background-image:
 radial-gradient(circle at 12% 18%,rgba(59,130,246,.07),transparent 32%),
 radial-gradient(circle at 85% 78%,rgba(34,197,94,.06),transparent 32%),
 linear-gradient(rgba(148,163,184,.045) 1px,transparent 1px),
 linear-gradient(90deg,rgba(148,163,184,.045) 1px,transparent 1px);
 background-size:auto,auto,32px 32px,32px 32px;}}
.block-container {{max-width:1150px;padding-top:3rem;padding-bottom:5rem;}}
header[data-testid="stHeader"] {{background:rgba(248,250,252,.95);}}
.stButton button {{border-radius:13px;min-height:44px;transition:transform .15s;}}
.stButton button:hover {{transform:translateY(-2px);}}
.hero {{text-align:center;padding:35px 10px 30px;}}
.hero h1 {{font-size:3.6rem;font-weight:800;color:#1e293b;margin-bottom:14px;}}
.hero p {{color:#64748b;margin:8px;}}
.home-card {{padding:24px;border:1px solid var(--color);border-radius:20px;
 background:var(--bg);min-height:165px;}}
.home-card h3 {{color:var(--color);margin:0 0 15px;}}
.home-card p {{color:#475569;}}
div.st-key-home_Formulas button {{border:2px solid #2563eb;color:#2563eb;background:#eff6ff;}}
div.st-key-home_Practice button {{border:2px solid #16a34a;color:#16a34a;background:#f0fdf4;}}
div.st-key-home_AI_Generator button {{border:2px solid #dc2626;color:#dc2626;background:#fef2f2;}}
.section-heading {{background:white;border:1px solid #e2e8f0;border-left:6px solid {accent};
 border-radius:18px;padding:23px;margin-bottom:23px;}}
.section-heading h2 {{color:{accent};margin:0;}}
.section-heading p {{color:#64748b;margin:8px 0 0;}}
.panel {{background:white;border:1px solid #e2e8f0;border-radius:20px;padding:23px;margin:15px 0;}}
.panel h3 {{color:#1e293b;}}
.mini-title {{font-weight:700;font-size:1.1rem;color:#1e293b;}}
.math-card {{border:1px solid #dbeafe;background:#f8fbff;border-radius:16px;padding:17px;
 margin:10px 0;color:#334155;min-height:115px;}}
.math-card h4 {{margin:0 0 8px;color:#1d4ed8;}}
.step-card {{border:1px solid #e2e8f0;border-radius:17px;padding:22px;background:white;min-height:125px;}}
.step-card h4 {{color:#1e293b;}}
div[data-testid="stSidebar"] {{background:white;border-right:1px solid #e2e8f0;}}
@media(max-width:650px) {{.hero h1 {{font-size:2.3rem;}} .home-card {{min-height:120px;}}}}
</style>
""", unsafe_allow_html=True)

# Consistent light theme and page-specific accents.
# CSS is deliberately scoped so native widgets stay readable.
PALE = {"Home": "#f1f5f9", "Formulas": "#eff6ff", "Practice": "#f0fdf4", "AI Generator": "#fef2f2"}
DEEP = {"Home": "#334155", "Formulas": "#1d4ed8", "Practice": "#15803d", "AI Generator": "#b91c1c"}
pale = PALE[page]
deep = DEEP[page]
st.markdown(f"""<style>
/* Stable notebook appearance */
.stApp {{color:#1e293b!important;}}
/* Notebook grid + geometric doodles, behind all app content. */
.stApp {{
 background-color:#f8fbff!important;
 background-image:
   url("{notebook_url}"),
   linear-gradient(rgba(77,113,158,.105) 1px,transparent 1px),
   linear-gradient(90deg,rgba(77,113,158,.105) 1px,transparent 1px),
   radial-gradient(ellipse at 12% 8%,rgba(37,99,235,.055),transparent 52%),
   radial-gradient(ellipse at 90% 88%,rgba(22,163,74,.055),transparent 55%)!important;
 background-size:850px 690px,32px 32px,32px 32px,auto,auto!important;
 background-position:center top,0 0,0 0,center,center!important;
 background-attachment:fixed!important;
}}
/* Notebook texture stays behind opaque content cards. */
[data-testid="stMainBlockContainer"] {{background:transparent!important;}}
header[data-testid="stHeader"] {{background:rgba(248,250,252,.96)!important;}}
/* SOLID SURFACES — no transparency in cards, alerts or content panels. */
/* Only the page background carries notebook drawings. */
[data-testid="stVerticalBlockBorderWrapper"]:has(> [data-testid="stVerticalBlock"]) {{
 background:#ffffff!important;background-image:none!important;
 border-radius:18px!important;
 box-shadow:0 6px 22px rgba(15,23,42,.10)!important;
}}
/* Streamlit renders bordered containers using this wrapper in newer versions. */
[data-testid="stVerticalBlockBorderWrapper"]:has(> [data-testid="stVerticalBlock"]) > [data-testid="stVerticalBlock"] {{
 background:#ffffff!important;background-image:none!important;
 border-radius:18px!important;
}}
/* All problem cards are keyed, so they receive a guaranteed opaque surface. */
[class*="st-key-practice_card_"] {{
 background:#ffffff!important;background-image:none!important;
 border:1.5px solid #b7ddc5!important;border-left:5px solid #16a34a!important;
 border-radius:17px!important;
 padding:14px 16px!important;
 box-shadow:0 6px 19px rgba(21,128,61,.10)!important;
 opacity:1!important;
}}
[class*="st-key-practice_card_"] > div,
[class*="st-key-practice_card_"] [data-testid="stVerticalBlock"],
[class*="st-key-practice_card_"] [data-testid="stVerticalBlockBorderWrapper"] {{
 background:#ffffff!important;background-image:none!important;
}}
/* Colored cards, messages, and formula surfaces are opaque too. */
.home-card,.step-card,.math-card,.panel,.section-heading,
[data-testid="stMetric"],[data-testid="stExpander"],
[data-testid="stAlert"],[data-testid="stNotification"] {{
 opacity:1!important;background-image:none!important;
 box-shadow:0 5px 18px rgba(15,23,42,.09)!important;
}}
.home-card {{background:var(--bg,#ffffff)!important;}}
.step-card,.panel {{background:#ffffff!important;}}
.math-card {{background:{pale}!important;}}
[data-testid="stAlert"],[data-testid="stNotification"] {{
 background:#eaf4ff!important;border:1.5px solid #b8d3f4!important;
 border-radius:15px!important;color:#1e293b!important;
}}
[data-testid="stAlert"] *,[data-testid="stNotification"] * {{color:#1e293b!important;opacity:1!important;}}
[data-testid="stExpander"] {{background:#ffffff!important;border:1px solid #dbe3ed!important;}}
[data-testid="stMetric"] {{background:{pale}!important;border:1px solid {accent}35!important;}}
.stApp button[data-testid="stBaseButton-secondary"] {{
 background:#ffffff!important;border:1.5px solid #cbd5e1!important;
 color:#1e293b!important;box-shadow:0 3px 12px rgba(15,23,42,.08)!important;
}}
.stApp button[data-testid="stBaseButton-secondary"] p {{color:inherit!important;opacity:1!important;}}
/* Colored identity for the active section */
.section-heading {{background:linear-gradient(115deg,{pale},#ffffff 85%)!important;
 border:1px solid {accent}45!important;border-left:7px solid {accent}!important;
 box-shadow:0 9px 28px {accent}12!important;}}
.section-heading h2 {{color:{accent}!important;}}
.stApp [data-testid="stButton"] button[kind="primary"],
.stApp button[data-testid="stBaseButton-primary"] {{background:{accent}!important;border:2px solid {accent}!important;color:white!important;
 box-shadow:0 4px 12px {accent}26!important;}}
.stApp button[data-testid="stBaseButton-secondary"]:hover {{border-color:{accent}!important;color:{deep}!important;background:{pale}!important;}}
/* Card highlights on section pages */
.math-card {{background:{pale}!important;border-color:{accent}50!important;}}
.math-card h4 {{color:{deep}!important;}}
[data-testid="stMetric"] {{border:1px solid {accent}35;border-radius:14px;padding:12px;background:{pale};}}
[data-testid="stMetricValue"] {{color:{deep}!important;}}
/* Sidebar: contrasting tinted surface, brand header, and navigation cards */
section[data-testid="stSidebar"] {{background:linear-gradient(165deg,#eaf0f9,#f8fafc 62%)!important;
 border-right:1px solid #cbd5e1!important;box-shadow:5px 0 22px rgba(30,41,59,.08)!important;}}
section[data-testid="stSidebar"] > div {{background:transparent!important;}}
.sidebar-brand {{background-color:{pale}!important;background-image:none!important;
 border:2px solid {accent}!important;border-left:7px solid {accent}!important;
 color:#172033!important;border-radius:20px;padding:21px 17px;margin:8px 0 18px;
 box-shadow:0 8px 22px rgba(15,23,42,.12)!important;opacity:1!important;}}
.sidebar-brand strong {{display:block;font-size:22px;letter-spacing:-.5px;color:{deep}!important;
 text-shadow:none!important;opacity:1!important;}}
.sidebar-brand small {{display:block;color:#475569!important;margin-top:5px;letter-spacing:.7px;
 font-weight:750;opacity:1!important;}}
.sidebar-label {{font-size:11px;letter-spacing:1.7px;color:#64748b!important;
 font-weight:800;margin:20px 0 10px 5px;}}
section[data-testid="stSidebar"] .stButton button {{min-height:53px!important;border-radius:14px!important;
 background:white!important;border:1px solid #dbe3ed!important;color:#334155!important;
 text-align:left!important;font-weight:650!important;box-shadow:0 2px 5px rgba(30,41,59,.035);}}
section[data-testid="stSidebar"] .stButton button:hover {{border-color:{accent}!important;background:{pale}!important;color:{deep}!important;}}
section[data-testid="stSidebar"] .st-key-sidebar_Formulas button {{border-left:5px solid #2563eb!important;}}
section[data-testid="stSidebar"] .st-key-sidebar_Practice button {{border-left:5px solid #16a34a!important;}}
section[data-testid="stSidebar"] .st-key-sidebar_AI_Generator button {{border-left:5px solid #dc2626!important;}}
section[data-testid="stSidebar"] .st-key-sidebar_{page.replace(' ','_')} button {{background:{pale}!important;border:2px solid {accent}!important;
 border-left:6px solid {accent}!important;color:{deep}!important;box-shadow:0 5px 13px {accent}1f!important;}}
section[data-testid="stSidebar"] .st-key-sidebar_home button {{background:#e2e8f0!important;}}
/* Preserve independent colors of the three home buttons */
div.st-key-home_Formulas button {{border:2px solid #2563eb!important;color:#1d4ed8!important;background:#eff6ff!important;}}
div.st-key-home_Practice button {{border:2px solid #16a34a!important;color:#15803d!important;background:#f0fdf4!important;}}
div.st-key-home_AI_Generator button {{border:2px solid #dc2626!important;color:#b91c1c!important;background:#fef2f2!important;}}

/* EVERY CONTENT PANEL is fully opaque, not just the Practice cards.
   Keyed containers are explicit: Home, Formulas, Practice detail screens. */
[class*="st-key-solid_"] {{
 background-color:#ffffff!important;
 background-image:none!important;
 opacity:1!important;
 border:1.5px solid #d1dbe8!important;
 border-left:5px solid {accent}!important;
 border-radius:18px!important;
 padding:20px!important;
 box-shadow:0 7px 22px rgba(15,23,42,.10)!important;
 isolation:isolate!important;
}}
/* Make sure nested layout wrappers don't undo the solid background. */
[data-testid="stVerticalBlockBorderWrapper"]:has([class*="st-key-solid_"]) {{
 background-color:#ffffff!important;
 background-image:none!important;
 border-radius:18px!important;
}}
/* Standard Streamlit status panels and expandable content */
[data-testid="stAlert"], [data-testid="stExpander"], [data-testid="stMetric"],
[data-testid="stToast"], [data-testid="stNotification"] {{
 background-color:#ffffff!important;
 background-image:none!important;
 opacity:1!important;
}}
/* Consistent colored info blocks without transparent surfaces. */
[data-testid="stAlert"] {{background-color:{pale}!important;}}
/* Explicit opaque backgrounds for custom content blocks on every page. */
.home-card,.step-card,.math-card,.panel,.section-heading,.sidebar-brand {{
 opacity:1!important;
 background-image:none!important;
}}
.section-heading {{background-color:{pale}!important;}}

/* Sidebar brand: ensure its text remains visible even if Streamlit wraps markdown. */
section[data-testid="stSidebar"] .sidebar-brand,
section[data-testid="stSidebar"] [class*="sidebar-brand"] {{
 background:{pale}!important;background-image:none!important;
 border:2px solid {accent}!important;border-left:7px solid {accent}!important;
 color:#172033!important;opacity:1!important;
}}
section[data-testid="stSidebar"] .sidebar-brand strong {{color:{deep}!important;}}
section[data-testid="stSidebar"] .sidebar-brand small {{color:#475569!important;}}

/* AI Generator: readable labels and inputs in the light theme. */
div.st-key-solid_ai_controls label, div.st-key-solid_ai_controls [data-testid="stWidgetLabel"],
div.st-key-solid_ai_controls [data-testid="stWidgetLabel"] p {{color:#334155!important;opacity:1!important;}}
div.st-key-solid_ai_controls [data-testid="stSelectbox"] [data-baseweb="select"] > div,
div.st-key-solid_ai_controls [data-testid="stTextArea"] textarea {{
 background:#ffffff!important;color:#172033!important;border:1.5px solid #cbd5e1!important;
 -webkit-text-fill-color:#172033!important;opacity:1!important;
}}
div.st-key-solid_ai_controls textarea::placeholder {{color:#64748b!important;opacity:1!important;}}
div.st-key-solid_ai_controls [data-baseweb="select"] span {{color:#172033!important;}}
/* Accessible contrast for the collapsed/expanded problem diagram control. */
[data-testid="stExpander"] summary,
[data-testid="stExpander"] summary *,
[data-testid="stExpander"] [data-testid="stExpanderToggleIcon"] {{
 color:#172b4d!important;opacity:1!important;
}}
[data-testid="stExpander"] summary {{background:#f1f5f9!important;border-radius:10px!important;}}
[data-testid="stExpander"] summary:hover {{background:#e2e8f0!important;}}
</style>""", unsafe_allow_html=True)

# Draw real, responsive SVG figures in a Streamlit HTML component.
# Dimensions control the drawing itself, not just the numeric results.
def diagram(kind, a=8, b=5, c=None, color="#2563eb"):
    a, b = float(a), float(b)
    c = float(c) if c is not None else None
    stroke = color
    # Hex with alpha: the shape's area has the same hue as its outline.
    fill = color + "30"

    def text(x, y, value, anchor="middle"):
        return (f'<text x="{x:.1f}" y="{y:.1f}" text-anchor="{anchor}" '
                f'fill="{"#eaf1fb" if dark else "#334155"}" font-size="15" font-family="Arial,sans-serif">'
                f'{html.escape(str(value))}</text>')

    def line(x1,y1,x2,y2,dashed=False):
        dash = ' stroke-dasharray="6 5"' if dashed else ''
        return f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{stroke}" stroke-width="2"{dash}/>'

    body = ''
    if kind in ("Rectangle", "Square"):
        # Uniform scaling, so the aspect ratio follows the slider values.
        scale = min(235/max(a, 1), 145/max(b, 1))
        w, h = a*scale, b*scale
        x, y = 180-w/2, 112-h/2
        body = f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" fill="{fill}" stroke="{stroke}" stroke-width="4" rx="3"/>'
        body += text(180,y-12,f'{a:g} cm') + text(x+w+32,y+h/2,f'{b:g} cm')
    elif kind in ("Triangle", "Right Triangle"):
        scale = min(225/max(a,1), 135/max(b,1))
        w,h = a*scale,b*scale
        x0,y0 = 180-w/2, 176
        if kind == "Right Triangle":
            apex = x0
        else:
            apex = x0+w*.38
        body = f'<polygon points="{x0:.1f},{y0:.1f} {x0+w:.1f},{y0:.1f} {apex:.1f},{y0-h:.1f}" fill="{fill}" stroke="{stroke}" stroke-width="4"/>'
        if kind == "Triangle":
            body += line(apex,y0-h,apex,y0,True)
        body += text(180,200,f'base = {a:g} cm') + text(apex-30,y0-h/2,f'h = {b:g} cm')
    elif kind == "Parallelogram":
        scale=min(210/max(a,1),125/max(b,1))
        w,h=a*scale,b*scale
        x0,y0=180-w/2,175
        skew=min(45,w*.3)
        body=f'<polygon points="{x0:.1f},{y0:.1f} {x0+w:.1f},{y0:.1f} {x0+w+skew:.1f},{y0-h:.1f} {x0+skew:.1f},{y0-h:.1f}" fill="{fill}" stroke="{stroke}" stroke-width="4"/>'
        body+=line(x0+skew,y0-h,x0+skew,y0,True)+text(180,199,f'base = {a:g} cm')+text(x0+skew-27,y0-h/2,f'h = {b:g}')
    elif kind == "Rhombus":
        scale=min(225/max(a,1),160/max(b,1))
        w,h=a*scale,b*scale
        body=f'<polygon points="180,{110-h/2:.1f} {180+w/2:.1f},110 180,{110+h/2:.1f} {180-w/2:.1f},110" fill="{fill}" stroke="{stroke}" stroke-width="4"/>'
        body+=line(180-w/2,110,180+w/2,110,True)+line(180,110-h/2,180,110+h/2,True)
        body+=text(180,209,f'd₁ = {a:g} cm; d₂ = {b:g} cm')
    elif kind == "Trapezoid":
        height=c if c is not None else 5
        scale=min(230/max(a,b,1),125/max(height,1))
        wt,wb,h=a*scale,b*scale,height*scale
        x1,x2=180-wt/2,180-wb/2
        body=f'<polygon points="{x1:.1f},{175-h:.1f} {x1+wt:.1f},{175-h:.1f} {x2+wb:.1f},175 {x2:.1f},175" fill="{fill}" stroke="{stroke}" stroke-width="4"/>'
        body+=text(180,163-h,f'{a:g} cm')+text(180,199,f'{b:g} cm')+text(325,175-h/2,f'h = {height:g}')
    elif kind in ("Circle", "Semicircle"):
        # Radius scales within the canvas while keeping a true circle.
        r=18+min(a,20)*3.1
        if kind == "Circle":
            body=f'<circle cx="180" cy="110" r="{r:.1f}" fill="{fill}" stroke="{stroke}" stroke-width="4"/>'
            body+=line(180,110,180+r,110)+text(180+r/2,100,f'r = {a:g}')
        else:
            body=f'<path d="M {180-r:.1f} 150 A {r:.1f} {r:.1f} 0 0 1 {180+r:.1f} 150 Z" fill="{fill}" stroke="{stroke}" stroke-width="4"/>'
            body+=text(180,175,f'r = {a:g} cm')
    elif kind == "Regular Polygon":
        n=int(c) if c is not None else 5
        import math
        radius=25+min(a,20)*4
        pts=[(180+radius*math.sin(2*math.pi*i/n),110-radius*math.cos(2*math.pi*i/n)) for i in range(n)]
        points=' '.join(f'{x:.1f},{y:.1f}' for x,y in pts)
        body=f'<polygon points="{points}" fill="{fill}" stroke="{stroke}" stroke-width="4"/>'
        body+=text(180,212,f'{n} sides; each {a:g} cm')
    else:
        body=text(180,110,'Diagram unavailable')

    markup=f'''<html><body style="margin:0;background:transparent;">
      <div style="background:{"#172235" if dark else "#f8fbff"};border:1px solid {"#34445c" if dark else "#e2e8f0"};border-radius:18px;padding:10px;text-align:center;box-sizing:border-box;">
      <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 360 225" role="img" aria-label="Interactive diagram of {html.escape(kind)}"
      style="display:block;width:100%;max-width:520px;height:245px;margin:auto;overflow:visible;">{body}</svg>
      </div></body></html>'''
    components.html(markup, height=280, scrolling=False)


SHAPES = [
    ("Rectangle", "▭", "A = a × b", "P = 2(a + b)", "a = length, b = width", "A classroom floor, a phone screen, or a garden."),
    ("Square", "□", "A = a²", "P = 4a", "a = side length", "A square tile or a chessboard square."),
    ("Triangle", "△", "A = b × h / 2", "P = a + b + c", "b = base, h = perpendicular height; a, b, c = side lengths for perimeter", "A triangular road sign or roof."),
    ("Right Triangle", "◺", "A = a × b / 2", "c = √(a² + b²)", "a, b = perpendicular legs; c = hypotenuse", "A ladder against a wall."),
    ("Parallelogram", "▱", "A = b × h", "P = 2(a + b)", "b = base, h = perpendicular height; a = other side", "A slanted paving stone."),
    ("Rhombus", "◇", "A = d₁ × d₂ / 2", "P = 4s", "d₁, d₂ = diagonals; s = side", "A diamond-shaped sign or decoration."),
    ("Trapezoid", "⏢", "A = (a + b) × h / 2", "P = a + b + c + d", "a, b = parallel bases; h = perpendicular height", "A trapezoid-shaped flower bed."),
    ("Circle", "◯", "A = πr²", "C = 2πr = πd", "r = radius, d = diameter = 2r; C = circumference", "A pizza, wheel, or round table."),
    ("Semicircle", "◠", "A = πr² / 2", "P = πr + 2r", "r = radius; perimeter includes the straight diameter", "A semicircular window."),
    ("Regular Polygon", "⬠", "A = P × apothem / 2", "P = n × s", "n = number of equal sides; s = side; apothem = center-to-side distance", "A regular pentagonal decoration."),
]
SHAPE_MAP = {s[0]: s for s in SHAPES}


def formula_explorer(name, key):
    st.markdown("#### Change the measurements")
    if name == "Rectangle":
        x, y = st.columns(2)
        with x: a = st.slider("Length a (cm)", 1, 20, 8, key=f"{key}_a")
        with y: b = st.slider("Width b (cm)", 1, 20, 5, key=f"{key}_b")
        area, perimeter = a*b, 2*(a+b)
        details = f"A = {a} × {b} = {area} cm²; P = 2({a} + {b}) = {perimeter} cm"
    elif name == "Square":
        a = st.slider("Side a (cm)", 1, 20, 6, key=f"{key}_a"); b = a
        area, perimeter = a*a, 4*a
        details = f"A = {a}² = {area} cm²; P = 4 × {a} = {perimeter} cm"
    elif name in ("Triangle", "Right Triangle"):
        x, y = st.columns(2)
        with x: a = st.slider("Base / first leg (cm)", 1, 20, 8, key=f"{key}_a")
        with y: b = st.slider("Height / second leg (cm)", 1, 20, 5, key=f"{key}_b")
        area = a*b/2
        if name == "Right Triangle":
            perimeter = a+b+math.hypot(a,b)
            details = f"A = {a} × {b} / 2 = {area:g} cm²; hypotenuse = √({a}² + {b}²) = {math.hypot(a,b):.2f} cm"
        else:
            perimeter = None
            details = f"A = {a} × {b} / 2 = {area:g} cm². Base and height alone do not determine perimeter."
    elif name == "Parallelogram":
        x, y = st.columns(2)
        with x: a = st.slider("Base (cm)", 1, 20, 9, key=f"{key}_a")
        with y: b = st.slider("Perpendicular height (cm)", 1, 20, 5, key=f"{key}_b")
        area, perimeter = a*b, None
        details = f"A = {a} × {b} = {area} cm². To find perimeter, we also need the slanted side length."
    elif name == "Rhombus":
        x, y = st.columns(2)
        with x: a = st.slider("Diagonal d₁ (cm)", 2, 20, 12, key=f"{key}_a")
        with y: b = st.slider("Diagonal d₂ (cm)", 2, 20, 8, key=f"{key}_b")
        area, perimeter = a*b/2, 4*math.hypot(a/2,b/2)
        details = f"A = {a} × {b} / 2 = {area:g} cm²; side = √(({a}/2)² + ({b}/2)²) = {perimeter/4:.2f} cm"
    elif name == "Trapezoid":
        x, y, z = st.columns(3)
        with x: a = st.slider("Top base (cm)", 1, 20, 6, key=f"{key}_a")
        with y: b = st.slider("Bottom base (cm)", 1, 20, 12, key=f"{key}_b")
        with z: c = st.slider("Height (cm)", 1, 20, 5, key=f"{key}_c")
        area, perimeter = (a+b)*c/2, None
        details = f"A = ({a} + {b}) × {c} / 2 = {area:g} cm². The two other side lengths are needed for perimeter."
    elif name in ("Circle", "Semicircle"):
        a = st.slider("Radius r (cm)", 1, 20, 5, key=f"{key}_a"); b = a
        area = math.pi*a*a*(.5 if name == "Semicircle" else 1)
        perimeter = math.pi*a+2*a if name == "Semicircle" else 2*math.pi*a
        details = f"Radius = {a} cm, diameter = {2*a} cm. Use π ≈ 3.14159."
    else:
        x, y = st.columns(2)
        with x: a = st.slider("Side length (cm)", 1, 20, 6, key=f"{key}_a")
        with y: c = st.slider("Number of sides", 3, 10, 5, key=f"{key}_c")
        # The apothem is determined by n and side length.
        b = a/(2*math.tan(math.pi/c))
        perimeter = c*a; area = perimeter*b/2
        details = f"For a regular {c}-gon, apothem is determined by the side length: {b:.2f} cm. A = P × apothem / 2."
        st.caption("The apothem is calculated automatically from the side length and number of sides.")
    diagram(name, a, b, c if name == "Trapezoid" else (c if name == "Regular Polygon" else None), color="#2563eb" if page == "Formulas" else "#16a34a" if page == "Practice" else "#6366f1")
    m1, m2 = st.columns(2)
    m1.metric("Area", f"{area:.2f} cm²" if isinstance(area,float) else f"{area} cm²")
    m2.metric("Perimeter", "Needs more information" if perimeter is None else f"{perimeter:.2f} cm" if isinstance(perimeter,float) else f"{perimeter} cm")
    st.info(details)


# A task has: title, question, shape, diagram dimensions, hint, worked solution, answer.
TASKS = {
"Basic": [
("Rectangle area", "A rectangle is 8 cm long and 5 cm wide. Find its area.","Rectangle",(8,5),"Multiply length by width.","A = 8 × 5 = 40 cm².","40 cm²"),
("Rectangle perimeter", "A rectangle is 12 m long and 4 m wide. Find its perimeter.","Rectangle",(12,4),"Add length and width, then multiply by 2.","P = 2(12 + 4) = 32 m.","32 m"),
("Square area", "A square has a side of 7 cm. Find its area.","Square",(7,7),"Multiply the side by itself.","A = 7² = 49 cm².","49 cm²"),
("Square perimeter", "A square has a side of 9 m. Find its perimeter.","Square",(9,9),"All four sides are equal.","P = 4 × 9 = 36 m.","36 m"),
("Triangle area", "A triangle has base 10 cm and height 6 cm. Find its area.","Triangle",(10,6),"A triangle is half of a matching parallelogram.","A = 10 × 6 / 2 = 30 cm².","30 cm²"),
("Right triangle area", "The perpendicular legs of a right triangle are 8 cm and 5 cm. Find its area.","Right Triangle",(8,5),"The legs can be the base and height.","A = 8 × 5 / 2 = 20 cm².","20 cm²"),
("Parallelogram area", "A parallelogram has base 11 cm and perpendicular height 4 cm. Find its area.","Parallelogram",(11,4),"Use base × perpendicular height.","A = 11 × 4 = 44 cm².","44 cm²"),
("Rhombus area", "A rhombus has diagonals of 10 cm and 6 cm. Find its area.","Rhombus",(10,6),"Multiply the diagonals and divide by 2.","A = 10 × 6 / 2 = 30 cm².","30 cm²"),
("Trapezoid area", "A trapezoid has parallel bases 6 cm and 10 cm, and height 4 cm. Find its area.","Trapezoid",(6,10,4),"Average the bases, then multiply by height.","A = (6 + 10) × 4 / 2 = 32 cm².","32 cm²"),
("Circle circumference", "A circle has radius 7 cm. Find its circumference in terms of π.","Circle",(7,7),"Circumference is 2πr.","C = 2 × π × 7 = 14π cm.","14π cm"),
("Circle area", "A circle has radius 3 cm. Find its area in terms of π.","Circle",(3,3),"Area is πr².","A = π × 3² = 9π cm².","9π cm²"),
("Find width", "A rectangle has area 48 cm² and length 8 cm. Find its width.","Rectangle",(8,6),"Rearrange A = length × width.","Width = A / length = 48 / 8 = 6 cm.","6 cm"),
("Find square side", "A square has perimeter 28 cm. Find its side length.","Square",(7,7),"Divide the perimeter by 4.","Side = 28 / 4 = 7 cm.","7 cm"),
("Semicircle area", "A semicircle has radius 4 cm. Find its area in terms of π.","Semicircle",(4,4),"Half of the area of a full circle.","A = π × 4² / 2 = 8π cm².","8π cm²"),
("Garden fencing", "A rectangular garden is 15 m long and 9 m wide. How much fencing is needed around it?","Rectangle",(15,9),"Fencing goes around the boundary.","P = 2(15 + 9) = 48 m.","48 m"),
],
"Standard": [
("Missing rectangle length", "A rectangle has area 96 cm² and width 8 cm. Find its length.","Rectangle",(12,8),"Length = area / width.","Length = 96 / 8 = 12 cm.","12 cm"),
("Square from area", "A square has area 144 cm². Find its perimeter.","Square",(12,12),"Take the square root to get the side.","Side = √144 = 12 cm; P = 4 × 12 = 48 cm.","48 cm"),
("Triangle missing height", "A triangle has area 42 cm² and base 14 cm. Find its height.","Triangle",(14,6),"From A = bh/2, h = 2A/b.","h = 2 × 42 / 14 = 6 cm.","6 cm"),
("Trapezoid height", "A trapezoid has area 60 cm² and bases 8 cm and 12 cm. Find its height.","Trapezoid",(8,12,6),"Use h = 2A/(a+b).","h = 2 × 60 / (8+12) = 6 cm.","6 cm"),
("Rhombus diagonal", "A rhombus has area 54 cm² and one diagonal 9 cm. Find the other diagonal.","Rhombus",(9,12),"Rearrange A = d₁d₂/2.","d₂ = 2 × 54 / 9 = 12 cm.","12 cm"),
("Parallelogram height", "A parallelogram has area 90 cm² and base 15 cm. Find its height.","Parallelogram",(15,6),"Divide area by base.","h = 90 / 15 = 6 cm.","6 cm"),
("Circle diameter", "A circular pond has circumference 20π m. Find its diameter.","Circle",(10,10),"C = πd.","d = 20π / π = 20 m.","20 m"),
("Circle from diameter", "A circle has diameter 14 cm. Find its area in terms of π.","Circle",(7,7),"Radius is half the diameter.","r = 14/2 = 7; A = 49π cm².","49π cm²"),
("Semicircle perimeter", "A semicircle has radius 6 cm. Find its perimeter in terms of π.","Semicircle",(6,6),"Include the curved arc AND the diameter.","P = πr + 2r = 6π + 12 cm.","6π + 12 cm"),
("Right triangle hypotenuse", "A right triangle has legs 6 cm and 8 cm. Find its hypotenuse.","Right Triangle",(6,8),"Use the Pythagorean theorem.","c = √(6² + 8²) = √100 = 10 cm.","10 cm"),
("Right triangle perimeter", "A right triangle has legs 5 cm and 12 cm. Find its perimeter.","Right Triangle",(5,12),"Find the hypotenuse first.","c = √(25+144)=13; P = 5+12+13=30 cm.","30 cm"),
("Floor tiles", "A 6 m by 4 m room is covered with square tiles of side 0.5 m. How many tiles are needed?","Rectangle",(6,4),"Divide room area by one tile's area.","Room area = 24 m²; tile area = 0.25 m²; 24/0.25 = 96 tiles.","96 tiles"),
("Rectangle vs square", "A rectangle is 10 cm by 6 cm. A square has the same perimeter. Find the square's area.","Rectangle",(10,6),"Find the rectangle's perimeter, then square side.","P = 2(10+6)=32; square side=32/4=8; area=64 cm².","64 cm²"),
("Triangle sign", "A triangular sign has base 1.2 m and height 0.8 m. Find its area.","Triangle",(12,8),"Use A = bh/2 with meters.","A = 1.2 × 0.8 / 2 = 0.48 m².","0.48 m²"),
("Regular pentagon perimeter", "A regular pentagon has side length 7 cm. Find its perimeter.","Regular Polygon",(7,5),"Five equal sides.","P = 5 × 7 = 35 cm.","35 cm"),
],
"Advanced": [
("Corner removed", "A 10 m by 8 m rectangular garden has a 4 m by 3 m rectangle removed from one corner. Find the remaining area.","Rectangle",(10,8),"Subtract the small rectangle's area.","A = 10×8 − 4×3 = 80−12 = 68 m².","68 m²"),
("Border around pool", "A 12 m by 8 m pool has a 1 m wide path around all sides. Find the path area.","Rectangle",(12,8),"Outer dimensions are 14 m by 10 m.","Path area = 14×10 − 12×8 = 140−96 = 44 m².","44 m²"),
("Shaded circle", "A circle of radius 5 cm is inside a square of side 10 cm. Find the area outside the circle but inside the square.","Circle",(5,5),"Subtract circle area from square area.","A = 10² − π×5² = 100−25π cm².","100 − 25π cm²"),
("Two concentric circles", "A ring has outer radius 9 cm and inner radius 6 cm. Find its area.","Circle",(9,9),"Subtract the smaller disk from the larger.","A = π(9²−6²)=π(81−36)=45π cm².","45π cm²"),
("Triangle in rectangle", "A triangle with base 12 cm and height 8 cm is cut from a 12 cm by 8 cm rectangle. Find the remaining area.","Triangle",(12,8),"The triangle takes half the rectangle's area.","Remaining = 12×8 − (12×8/2) = 48 cm².","48 cm²"),
("Trapezoid garden", "A trapezoid garden has bases 14 m and 20 m and height 9 m. Grass costs $4 per m². Find total cost.","Trapezoid",(14,20,9),"Find the area before multiplying by the cost.","A=(14+20)×9/2=153 m²; cost=153×4=$612.","$612"),
("Rhombus perimeter", "A rhombus has diagonals 16 cm and 12 cm. Find its perimeter.","Rhombus",(16,12),"Half-diagonals form a right triangle.","Side=√(8²+6²)=10 cm; P=4×10=40 cm.","40 cm"),
("Semicircular window", "A semicircular window has diameter 10 cm. Find its full perimeter in terms of π.","Semicircle",(5,5),"Include the straight edge.","r=5; P=π×5+10 = 5π+10 cm.","5π + 10 cm"),
("Find radius from area", "A circle has area 81π cm². Find its circumference.","Circle",(9,9),"First find r using πr² = 81π.","r=9; C=2π×9=18π cm.","18π cm"),
("Similar rectangles", "A rectangle is 6 cm by 4 cm. Both dimensions are tripled. By what factor does its area increase?","Rectangle",(6,4),"Area scales with the square of the scale factor.","Old area=24; new area=18×12=216; 216/24=9.","9 times"),
("Same area, new width", "A 12 cm by 8 cm rectangle is changed to one with the same area but length 16 cm. Find its new perimeter.","Rectangle",(12,8),"Keep area constant.","Area=96; new width=96/16=6; P=2(16+6)=44 cm.","44 cm"),
("Pythagorean ladder", "A 13 m ladder leans against a wall. Its base is 5 m from the wall. How high does it reach?","Right Triangle",(5,12),"Ladder is the hypotenuse.","h=√(13²−5²)=√144=12 m.","12 m"),
("Composite floor", "A floor consists of a 9 m by 6 m rectangle and an attached 3 m by 4 m rectangle without overlap. Find total area.","Rectangle",(9,6),"Add the two rectangular areas.","A=9×6+3×4=54+12=66 m².","66 m²"),
("Regular hexagon", "A regular hexagon has side length 6 cm. Find its exact area.","Regular Polygon",(6,5),"Split it into six equilateral triangles.","Each triangle area=√3×6²/4=9√3; total=6×9√3=54√3 cm².","54√3 cm²"),
("Compare circles", "A circle's radius increases from 4 cm to 6 cm. How much does its area increase in terms of π?","Circle",(6,6),"Subtract the two circle areas.","Increase=π(6²−4²)=π(36−16)=20π cm².","20π cm²"),
]}
assert all(len(items) == 15 for items in TASKS.values())


def advanced_diagram(idx):
    """Task-specific composite drawings for all 15 advanced questions."""
    stroke = "#60a5fa" if dark else "#2563eb"
    fill = "#3b82f644"
    cut = "#172235" if dark else "#ffffff"
    label = "#eaf1fb" if dark else "#243247"
    def rect(x,y,w,h,paint=fill):
        return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{paint}" stroke="{stroke}" stroke-width="3"/>'
    def txt(x,y,t,size=15):
        return f'<text x="{x}" y="{y}" fill="{label}" font-family="Arial" font-size="{size}" text-anchor="middle">{html.escape(str(t))}</text>'
    def circ(cx,cy,r,paint=fill):
        return f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{paint}" stroke="{stroke}" stroke-width="3"/>'
    parts = ''
    note = ''
    if idx == 0: # Corner removed: L-shaped polygon
        parts = '<path d="M80 55 H300 V140 H210 V215 H80 Z" fill="'+fill+'" stroke="'+stroke+'" stroke-width="4"/>'
        parts += '<path d="M210 140 H300 V215 H210 Z" fill="none" stroke="'+stroke+'" stroke-dasharray="5 5" opacity=".35"/>'
        parts += txt(190,43,'10 m')+txt(62,140,'8 m')+txt(256,132,'4 m')+txt(322,184,'3 m')
        note='The upper-right 4 m × 3 m corner is removed (the notch is not part of the garden).'
        # Correct 4/10 width and 3/8 height: draw from top-right corner, not bottom-right
        parts = '<path d="M80 55 H212 V118 H300 V215 H80 Z" fill="'+fill+'" stroke="'+stroke+'" stroke-width="4"/>'
        parts += '<path d="M212 55 H300 V118" fill="none" stroke="'+stroke+'" stroke-dasharray="5 5" stroke-width="2" opacity=".6"/>'
        parts += txt(190,43,'10 m')+txt(58,145,'8 m')+txt(255,83,'4 m')+txt(317,95,'3 m')
    elif idx == 1:
        parts = rect(80,45,230,175)+rect(97,62,196,141,cut)+txt(195,35,'14 m outer')+txt(195,143,'12 m × 8 m pool')+txt(326,132,'1 m path')
        note='The blue border is a 1 m wide path on all four sides.'
    elif idx == 2:
        parts=rect(95,45,190,190)+circ(190,140,95,cut)+txt(190,30,'square: 10 cm')+txt(190,142,'r = 5 cm')
        note='Find the colored corners: square area minus circle area.'
    elif idx == 3:
        parts=circ(190,140,95)+circ(190,140,63,cut)+txt(190,33,'outer r = 9 cm')+txt(190,143,'inner r = 6 cm')
        note='The colored annulus is the outer circle minus the inner circle.'
    elif idx == 4:
        parts=rect(85,55,210,150)+f'<polygon points="85,205 295,205 85,55" fill="{cut}" stroke="{stroke}" stroke-width="2"/>'+txt(190,42,'12 cm')+txt(317,137,'8 cm')
        note='The white triangle is removed; find the blue region.'
    elif idx == 5:
        parts=f'<polygon points="130,55 260,55 310,205 80,205" fill="{fill}" stroke="{stroke}" stroke-width="4"/>'+txt(195,43,'14 m')+txt(195,228,'20 m')+txt(194,143,'height = 9 m')
        note='Find the trapezoid area, then multiply by $4 per m².'
    elif idx == 6:
        parts=f'<polygon points="190,43 280,140 190,237 100,140" fill="{fill}" stroke="{stroke}" stroke-width="4"/><path d="M100 140 H280 M190 43 V237" stroke="{stroke}" stroke-dasharray="6 5" stroke-width="2"/>'+txt(190,31,'12 cm diagonal')+txt(285,151,'16 cm diagonal')
        note='The diagonals bisect each other at right angles.'
    elif idx == 7:
        parts=f'<path d="M95 165 A95 95 0 0 1 285 165 Z" fill="{fill}" stroke="{stroke}" stroke-width="4"/>'+txt(190,190,'diameter = 10 cm')
        note='The perimeter includes the curved arc and the straight diameter.'
    elif idx == 8:
        parts=circ(190,140,85)+f'<line x1="190" y1="140" x2="275" y2="140" stroke="{stroke}" stroke-width="3"/>'+txt(231,129,'r = 9 cm')
        note='The given area 81π determines the radius.'
    elif idx == 9:
        parts=rect(35,85,90,60)+rect(190,45,135,90)+txt(80,75,'6 × 4')+txt(257,35,'18 × 12')+txt(170,155,'× 3 →')
        note='Both dimensions triple; the area increases by 3².'
    elif idx == 10:
        parts=rect(30,85,140,95)+rect(225,100,125,71)+txt(100,75,'12 × 8')+txt(286,90,'16 × 6')+txt(196,144,'→')
        note='Both rectangles have area 96 cm², but different perimeters.'
    elif idx == 11:
        parts=f'<polygon points="105,210 295,210 295,50" fill="{fill}" stroke="{stroke}" stroke-width="4"/>'+txt(198,230,'5 m from wall')+txt(322,136,'12 m')+txt(173,123,'13 m ladder')
        note='The ladder is the hypotenuse of a right triangle.'
    elif idx == 12:
        parts=f'<path d="M65 60 H245 V130 H305 V215 H65 Z" fill="{fill}" stroke="{stroke}" stroke-width="4"/>'+txt(156,48,'9 m')+txt(47,146,'6 m')+txt(274,121,'3 m')+txt(319,176,'4 m')
        note='Two rectangles are joined without overlapping. Add their areas.'
    elif idx == 13:
        import math as _math
        pts=[(190+92*_math.cos(_math.pi/6+i*_math.pi/3),140+92*_math.sin(_math.pi/6+i*_math.pi/3)) for i in range(6)]
        coords=' '.join(f'{x:.1f},{y:.1f}' for x,y in pts)
        parts=f'<polygon points="{coords}" fill="{fill}" stroke="{stroke}" stroke-width="4"/>'
        for x,y in pts: parts+=f'<line x1="190" y1="140" x2="{x:.1f}" y2="{y:.1f}" stroke="{stroke}" stroke-dasharray="5 5"/>'
        parts+=txt(190,255,'each side = 6 cm')
        note='The hexagon consists of six equilateral triangles.'
    else:
        parts=circ(115,140,53)+circ(275,140,80)+txt(115,238,'r = 4 cm')+txt(275,238,'r = 6 cm')
        note='Subtract the smaller circle area from the larger circle area.'
    doc=f"""<html><body style="margin:0;background:transparent;color:{label};font-family:Arial,sans-serif">
    <div style="border:1px solid {'#34445c' if dark else '#dce5f0'};background:{'#172235' if dark else '#f8fbff'};border-radius:18px;padding:14px;text-align:center">
    <svg viewBox="0 0 390 265" style="display:block;max-width:520px;width:100%;height:270px;margin:auto">{parts}</svg>
    <p style="font-size:13px;line-height:1.45;margin:8px 0">{html.escape(note)}</p>
    </div></body></html>"""
    components.html(doc,height=350,scrolling=False)


def section_header(title, description):
    st.markdown(f'<div class="section-heading"><h2>{html.escape(title)}</h2><p>{html.escape(description)}</p></div>', unsafe_allow_html=True)


def get_gemini_key():
    """Read a private key from Streamlit secrets or the environment."""
    try:
        key = st.secrets.get("GEMINI_API_KEY", "")
        if key:
            return str(key).strip()
    except (FileNotFoundError, KeyError, OSError):
        pass
    return os.environ.get("GEMINI_API_KEY", "").strip()


def _gemini_models(key):
    """Discover compatible text models for this key; cached to avoid repeated calls."""
    endpoint = "https://generativelanguage.googleapis.com/v1beta/models"
    names = []
    token = None
    for _ in range(5):
        params = {"pageSize": 100}
        if token:
            params["pageToken"] = token
        request = Request(endpoint + "?" + urlencode(params), headers={"x-goog-api-key": key})
        with urlopen(request, timeout=18) as response:
            data = json.load(response)
        for model in data.get("models", []):
            actions = model.get("supportedGenerationMethods", model.get("supportedActions", []))
            name = model.get("name", "").removeprefix("models/")
            if "generateContent" in actions and name.startswith("gemini-") and not any(
                x in name for x in ("audio", "tts", "image", "live", "robotics", "computer-use", "embedding", "native")
            ):
                names.append(name)
        token = data.get("nextPageToken")
        if not token:
            break
    # Prefer light, fast text models, then other Flash models; avoid research/pro models.
    def priority(name):
        return (0 if "flash-lite" in name else 1 if "flash" in name else 2,
                1 if "preview" in name else 0, name)
    return sorted(set(names), key=priority)


@st.cache_data(ttl=3600, show_spinner=False)
def available_gemini_models(_key):
    return _gemini_models(_key)


def _send_gemini(key, model, prompt):
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.5, "responseMimeType": "application/json", "maxOutputTokens": 3000},
    }
    endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/{quote(model, safe='')}:generateContent"
    request = Request(endpoint, data=json.dumps(payload).encode("utf-8"),
                      headers={"Content-Type": "application/json", "x-goog-api-key": key}, method="POST")
    with urlopen(request, timeout=50) as response:
        return json.load(response)


def clean_ai_text(value):
    """Normalize Gemini's occasional code-style formatting for school math."""
    if not value:
        return ""
    value = str(value)
    # Remove only Markdown formatting markers; preserve all mathematical content.
    value = re.sub(r"```(?:[a-zA-Z0-9_-]+)?\s*([\s\S]*?)```", r"\1", value)
    value = re.sub(r"`([^`\n]+)`", r"\1", value)
    return value.strip()


def validate_ai_diagram(spec):
    """Validate a coordinate diagram against explicit mathematical constraints.

    The model must supply coordinates in actual problem units, plus named points
    and verifiable constraints. Unverifiable drawings are withheld.
    """
    if not isinstance(spec, dict):
        return False, "No coordinate-verified diagram was provided."
    points = spec.get("points")
    checks = spec.get("checks")
    if not isinstance(points, dict) or not isinstance(checks, list) or not checks:
        return False, "Diagram has no named coordinates and geometric checks."
    if not 3 <= len(points) <= 24:
        return False, "Invalid number of diagram points."
    try:
        for name, xy in points.items():
            if not isinstance(name, str) or not re.fullmatch(r"[A-Za-z][A-Za-z0-9_]{0,9}", name):
                raise ValueError("Invalid point name")
            if not isinstance(xy, list) or len(xy) != 2 or any(
                isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v) or abs(v) > 100000
                for v in xy
            ):
                raise ValueError("Invalid coordinates")
        def pt(name):
            if name not in points:
                raise ValueError("Unknown point")
            return points[name]
        def vec(a, b):
            x, y = pt(a), pt(b)
            return (y[0]-x[0], y[1]-x[1])
        def length(a, b):
            return math.hypot(*vec(a,b))
        def cross(u,v):
            return u[0]*v[1]-u[1]*v[0]
        def dot(u,v):
            return u[0]*v[0]+u[1]*v[1]
        for check in checks:
            typ = check["type"]
            if typ == "length":
                actual = length(check["a"],check["b"])
                expected = float(check["value"])
                if expected <= 0 or not math.isclose(actual,expected,rel_tol=1e-5,abs_tol=1e-5):
                    raise ValueError("Length mismatch")
            elif typ in ("parallel","perpendicular"):
                u=vec(check["a"],check["b"])
                v=vec(check["c"],check["d"])
                scale=math.hypot(*u)*math.hypot(*v)
                if scale < 1e-10:
                    raise ValueError("Degenerate segment")
                error = abs(cross(u,v) if typ=="parallel" else dot(u,v))/scale
                if error > 1e-5:
                    raise ValueError("Angle mismatch")
            elif typ == "on_segment":
                p=pt(check["p"]); a=pt(check["a"]); b=pt(check["b"])
                u=vec(check["a"],check["b"])
                v=(p[0]-a[0],p[1]-a[1])
                d=dot(u,u)
                if d < 1e-10 or abs(cross(u,v)) > 1e-5*d or not -1e-5 <= dot(v,u)/d <= 1+1e-5:
                    raise ValueError("Point does not lie on segment")
            else:
                raise ValueError("Unsupported geometric check")
        polygons=spec.get("polygons",[])
        segments=spec.get("segments",[])
        if not isinstance(polygons,list) or not isinstance(segments,list) or not polygons:
            raise ValueError("Invalid drawing structure")
        for poly in polygons:
            names=poly["points"]
            if not isinstance(names,list) or not 3 <= len(names) <= 12:
                raise ValueError("Invalid polygon")
            for name in names: pt(name)
            # Reject degenerate polygons.
            area=sum(pt(names[i])[0]*pt(names[(i+1)%len(names)])[1] -
                     pt(names[(i+1)%len(names)])[0]*pt(names[i])[1]
                     for i in range(len(names)))/2
            if abs(area)<1e-8:
                raise ValueError("Degenerate polygon")
        for seg in segments:
            pt(seg["from"]);pt(seg["to"])
        return True, ""
    except (KeyError,TypeError,ValueError,OverflowError,ZeroDivisionError) as exc:
        return False, str(exc)


def render_ai_diagram(spec):
    """Only draw coordinate-checked geometry; never trust a freehand AI sketch."""
    valid, _ = validate_ai_diagram(spec)
    if not valid:
        return False
    points=spec["points"]
    all_x=[v[0] for v in points.values()]
    all_y=[v[1] for v in points.values()]
    xmin,xmax=min(all_x),max(all_x)
    ymin,ymax=min(all_y),max(all_y)
    span=max(xmax-xmin,ymax-ymin,1)
    scale=min(450/max(xmax-xmin,1e-9),215/max(ymax-ymin,1e-9))
    def xy(name):
        x,y=points[name]
        return (285+(x-(xmin+xmax)/2)*scale,150-(y-(ymin+ymax)/2)*scale)
    shapes=[]
    for poly in spec.get("polygons",[])[:8]:
        coords=" ".join(f"{xy(name)[0]:.1f},{xy(name)[1]:.1f}" for name in poly["points"])
        shapes.append(f'<polygon points="{coords}" fill="#fee2e2" stroke="#dc2626" stroke-width="3"/>')
    for seg in spec.get("segments",[])[:24]:
        a,b=xy(seg["from"]),xy(seg["to"])
        dash=' stroke-dasharray="7 6"' if seg.get("dashed") else ''
        shapes.append(f'<line x1="{a[0]:.1f}" y1="{a[1]:.1f}" x2="{b[0]:.1f}" y2="{b[1]:.1f}" stroke="#2563eb" stroke-width="3"{dash}/>')
    for name in points:
        x,y=xy(name)
        shapes.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3.5" fill="#1e293b"/>')
        shapes.append(f'<text x="{x+9:.1f}" y="{y-9:.1f}" font-size="14" fill="#172554" font-weight="bold">{html.escape(name)}</text>')
    for label in spec.get("labels",[])[:18]:
        if not isinstance(label,dict) or label.get("at") not in points:
            continue
        x,y=xy(label["at"])
        shapes.append(f'<text x="{x:.1f}" y="{y+23:.1f}" text-anchor="middle" font-size="14" fill="#172554" paint-order="stroke" stroke="#fff" stroke-width="4">{html.escape(str(label.get("text",""))[:35])}</text>')
    svg=''.join(shapes)
    components.html(f"""<html><body style="margin:0;font-family:Arial;background:white">
    <div style="background:#f8fbff;border:1px solid #dbeafe;border-radius:14px;padding:12px">
    <svg viewBox="0 0 570 310" style="width:100%;height:250px;display:block" role="img" aria-label="Coordinate-checked geometry diagram">{svg}</svg>
    <div style="text-align:center;color:#64748b;font-size:12px">Coordinate-based schematic · Verified geometric constraints</div>
    </div></body></html>""",height=290,scrolling=False)
    return True


def display_solution_steps(solution):
    """Display Gemini's numbered steps in compact, solid cards."""
    cleaned = clean_ai_text(solution)
    pattern = r"(?i)(?<![\\w.])(?:step\\s+)?(\\d{1,2})[.):]\\s+"
    matches = list(re.finditer(pattern, cleaned))

    def format_math(text):
        # Improve simple spoken exponent notation without changing calculations.
        text = re.sub(r"(?i)\\b([a-z]|\\d+)\\s+squared\\b", r"\\1²", text)
        return html.escape(text.strip()).replace("\\n", "<br>")

    if matches and matches[0].group(1) == "1":
        sections = []
        preface = cleaned[:matches[0].start()].strip()
        if preface:
            sections.append(f'<p style="margin:0 0 8px">{format_math(preface)}</p>')
        for i, match in enumerate(matches):
            end = matches[i + 1].start() if i + 1 < len(matches) else len(cleaned)
            body = cleaned[match.end():end].strip()
            if body:
                sections.append(
                    '<div style="background:#f5f8ff;border:1px solid #dbe5f4;'
                    'border-left:4px solid #e32629;border-radius:11px;'
                    'padding:10px 14px;margin:0 0 8px;line-height:1.55;">'
                    f'<div style="font-weight:750;color:#172b4d;margin-bottom:3px;">'
                    f'Step {html.escape(match.group(1))}</div>'
                    f'<div style="color:#223047;">{format_math(body)}</div></div>'
                )
        st.markdown("".join(sections), unsafe_allow_html=True)
    else:
        paragraphs = re.split(r"\\n\\s*\\n|\\n(?=\\s*[-•])", cleaned)
        for paragraph in paragraphs:
            if paragraph.strip():
                st.markdown(
                    '<div style="background:#f5f8ff;border:1px solid #dbe5f4;'
                    'border-radius:10px;padding:10px 14px;margin-bottom:8px;">'
                    + format_math(paragraph) + "</div>",
                    unsafe_allow_html=True,
                )


def _request_json_with_fallback(key, models, prompt, max_models=5):
    """Call Gemini with bounded retries; never silently accept invalid JSON."""
    errors = []
    for model in models[:max_models]:
        for attempt in range(2):
            try:
                raw = _send_gemini(key, model, prompt)
                content = "".join(part.get("text", "") for part in raw["candidates"][0]["content"]["parts"])
                obj = json.loads(content)
                if not isinstance(obj, dict):
                    raise ValueError("Expected a JSON object")
                return obj
            except HTTPError as exc:
                if exc.code in (401, 403):
                    raise RuntimeError("Gemini authentication failed. Check your API key and permissions.") from exc
                if exc.code == 429:
                    raise RuntimeError("Gemini rate limit or quota reached. Try later or check AI Studio usage.") from exc
                errors.append(f"{model}: HTTP {exc.code}")
                if exc.code in (500, 502, 503, 504) and attempt == 0:
                    time.sleep(1.5 + random.random())
                    continue
                break
            except (URLError, TimeoutError) as exc:
                errors.append(f"{model}: connection problem")
                if attempt == 0:
                    time.sleep(1)
                    continue
                break
            except (KeyError, IndexError, TypeError, ValueError, json.JSONDecodeError):
                errors.append(f"{model}: invalid JSON response")
                break
    raise RuntimeError("Gemini could not return a valid response. " + "; ".join(errors[:4]))


def _verify_geometry_problem(key, models, problem, level, topic):
    """Separate AI review. It is a useful filter, not a mathematical proof."""
    verification_prompt = f"""You are an independent, strict geometry exam reviewer for grades 5–9.
Check this proposed problem WITHOUT trusting its supplied solution. Independently solve it first.
Check that all quantities, geometric relationships and units are defined; the answer is uniquely determined;
any construction is possible; all calculations and units in the proposed solution and final answer are correct;
the wording is unambiguous; and the level ({level}) and topic ({topic}) are appropriate.\nIf a diagram_spec is supplied, check that the depicted geometry, labels and relationships match the written problem. Reject misleading diagrams.
If a triangle or composite figure is not fully specified, REJECT it. Do not invent missing dimensions.
Check particularly whether every claimed point lies on its stated finite segment
(not just its infinite extension). Check perpendicular foot locations algebraically.
For isosceles trapezoids, calculate the height and verify any intersection.
A diagram's check list does not prove the question correct; independently test its
relationships and whether all relevant dimensions are represented.
If there is any material ambiguity or error, reject rather than guess.
Return ONLY a JSON object with fields:
"valid" (boolean), "reason" (short string), "independent_answer" (string).
Proposed task JSON:
{json.dumps(problem, ensure_ascii=False)}"""
    review = _request_json_with_fallback(key, models, verification_prompt, max_models=4)
    if type(review.get("valid")) is not bool or not isinstance(review.get("reason"), str):
        raise ValueError("Reviewer returned an incomplete verdict")
    if review["valid"] and not str(review.get("independent_answer", "")).strip():
        raise ValueError("Reviewer did not independently calculate an answer")
    return review


def generate_geometry_problem(level, topic, request_text):
    """Generate, independently review, and reject questionable tasks."""
    key = get_gemini_key()
    if not key:
        raise ValueError("Gemini API key is not configured. Add it to .streamlit/secrets.toml.")
    try:
        models = available_gemini_models(key)
    except HTTPError as exc:
        raise RuntimeError(f"Could not retrieve Gemini models (HTTP {exc.code}).") from exc
    except (URLError, TimeoutError) as exc:
        raise RuntimeError("Could not connect to Gemini. Check your internet connection.") from exc
    if not models:
        raise RuntimeError("No text-generation models are available for this Gemini API key.")
    override = os.environ.get("GEMINI_MODEL", "").strip().removeprefix("models/")
    if override:
        models = [override] + [m for m in models if m != override]
    base_prompt = f"""You are a careful geometry tutor for grades 5–9.
Create exactly ONE original, mathematically correct geometry word problem in English.
Difficulty: {level}. Topic: {topic}.
Student preferences: {request_text[:700] if request_text.strip() else 'No additional preferences.'}
Basic = one/two steps; Standard = several steps; Advanced = multi-step reasoning, grade 9 or below.
Avoid unnecessarily complicated stories. Do not use calculus or advanced trigonometry.
CRITICAL: the problem must have enough explicitly stated information for exactly one numerical answer.
For composite figures, precisely explain which pieces touch, overlap, are removed, or share dimensions.
Solve the problem independently before writing the question. Verify all arithmetic, geometry and units.
Return ONLY a JSON object with these STRING fields:
"title", "question", "hint", "solution", "answer", "concept", "diagram_description".
Explain the solution in numbered steps, with each step on its own line; hint must not reveal the final answer.
Only include a diagram_spec if you can represent the exact geometry using actual
Cartesian coordinates in the SAME measurement units as the problem. Never use arbitrary
0..100 drawing coordinates. Coordinates must be mathematically consistent with all
stated side lengths, point locations, and angles. If a perpendicular meets only the
EXTENSION of a segment, do not claim it meets the segment itself: rewrite the problem.
The optional diagram_spec has this format:
{{"points":{{"A":[0,0],"B":[8,0],"C":[8,6],"D":[0,6]}},
"polygons":[{{"points":["A","B","C","D"]}}],
"segments":[{{"from":"A","to":"C","dashed":true}}],
"checks":[{{"type":"length","a":"A","b":"B","value":8}},
{{"type":"length","a":"B","b":"C","value":6}},
{{"type":"perpendicular","a":"A","b":"B","c":"B","d":"C"}},
{{"type":"parallel","a":"A","b":"B","c":"D","d":"C"}},
{{"type":"on_segment","p":"B","a":"A","b":"B"}}],
"labels":[{{"at":"A","text":"8 m"}}]}}.
For checks, use lengths for all explicitly given segment lengths; use parallel,
perpendicular and on_segment for ALL such relationships asserted in the question.
The checks are executable geometric requirements, not decorative descriptions.
Every named geometric vertex must be included. Do not draw a line to an invented
intersection. If you cannot make a reliable coordinate diagram, omit diagram_spec.
The question must be geometrically possible even when diagram_spec is omitted.
No Markdown backticks, code blocks, or programming-style formatting. Use plain text for math and money."""
    required = ("title", "question", "hint", "solution", "answer", "concept", "diagram_description")
    rejected_reasons = []
    # At most three candidates, each checked in a separate API request.
    for candidate_number in range(3):
        feedback = ""
        if rejected_reasons:
            feedback = "\nPrevious attempt was rejected. Avoid this issue: " + rejected_reasons[-1][:350]
        problem = _request_json_with_fallback(key, models, base_prompt + feedback)
        if any(not isinstance(problem.get(k), str) or not problem[k].strip() for k in required):
            rejected_reasons.append("Missing or empty required field")
            continue
        diagram_spec = problem.get("diagram_spec")
        problem = {k: clean_ai_text(problem[k]) for k in required}
        if isinstance(diagram_spec, dict):
            ok, reason = validate_ai_diagram(diagram_spec)
            if not ok:
                rejected_reasons.append("Diagram failed coordinate checks: " + reason)
                continue
            problem["diagram_spec"] = diagram_spec
        try:
            review = _verify_geometry_problem(key, models, problem, level, topic)
        except (ValueError, RuntimeError) as exc:
            # Fail closed: no review means no 'verified' problem.
            rejected_reasons.append("Verification unavailable: " + str(exc)[:150])
            continue
        if review["valid"]:
            problem["verification_status"] = "AI-reviewed"
            problem["verification_note"] = "A separate Gemini review checked the data, solution and answer. This is not a formal guarantee."
            return problem
        rejected_reasons.append(review["reason"] or "Reviewer rejected the problem")
    raise RuntimeError("Gemini could not produce a problem that passed the separate math review after 3 attempts. "
                       "Try another topic or simplify your request. Last issue: " + rejected_reasons[-1][:200])


if page == "Home":
    st.markdown('<style>[data-testid="stSidebar"],[data-testid="collapsedControl"]{display:none!important;}</style>', unsafe_allow_html=True)
    st.markdown('<div class="hero"><h1>AI Math Tutor</h1><p>Learn geometry in your own way.</p><p>Explore formulas, practice your skills, and create new problems with AI.</p></div>', unsafe_allow_html=True)
    cards = [("📘 Formulas","Explore shapes and understand their formulas.","#2563eb","#eff6ff","Formulas"),
             ("✏️ Practice","Solve 45 problems with hints and solutions.","#16a34a","#f0fdf4","Practice"),
             ("✨ AI Generator","Create personalized geometry challenges with Gemini AI.","#dc2626","#fef2f2","AI Generator")]
    for col, (title, desc, color, bg, dest) in zip(st.columns(3, gap="large"), cards):
        with col:
            st.markdown(f'<div class="home-card" style="--color:{color};--bg:{bg}"><h3>{title}</h3><p>{desc}</p></div>', unsafe_allow_html=True)
            if st.button("Open " + dest + " →", key="home_"+dest.replace(" ","_"), use_container_width=True):
                navigate(dest)
    st.write("")
    st.markdown("## How It Works")
    for col, (title, desc) in zip(st.columns(3), [("01 · 📖 Learn","Explore formulas and change measurements."),
                                                     ("02 · ✏️ Practice","Try problems and reveal hints when needed."),
                                                     ("03 · ✨ Improve","Generate new questions with Gemini AI.")]):
        with col:
            st.markdown(f'<div class="step-card"><h4>{title}</h4><p>{desc}</p></div>', unsafe_allow_html=True)
    st.write("")
    st.markdown("## Geometry in Action")
    st.caption("Move the sliders to see how a rectangle changes. Its area and perimeter update instantly.")
    with st.container(border=True, key="solid_home_explorer"):
        formula_explorer("Rectangle", "home_rectangle")
    st.caption("AI Math Tutor · Geometry for grades 5–9")

else:
    with st.sidebar:
        st.markdown('<div class="sidebar-brand"><strong>📐 AI Math Tutor</strong><small>GEOMETRY LEARNING STUDIO</small></div>', unsafe_allow_html=True)
        st.markdown('<div class="sidebar-label">YOUR WORKSPACE</div>', unsafe_allow_html=True)
        if st.button("🏠  Main Menu", key="sidebar_home", use_container_width=True): navigate("Home")
        st.markdown('<div class="sidebar-label">EXPLORE</div>', unsafe_allow_html=True)
        for dest, label in [("Formulas","📘  Formulas"),("Practice","✏️  Practice"),("AI Generator","✨  AI Generator")]:
            if st.button(label, key="sidebar_"+dest.replace(" ","_"), use_container_width=True): navigate(dest)
        st.markdown(f'<div style="margin-top:28px;padding:14px;border-radius:14px;background:{pale};border:1px solid {accent}35;color:#475569;font-size:13px"><b style="color:{deep}">Currently exploring</b><div style="margin-top:5px">{html.escape(page)}</div></div>', unsafe_allow_html=True)

    if page == "Formulas":
        if st.session_state.shape is None:
            section_header("Formula Library", "Choose a shape to open its interactive formula lesson.")
            st.caption("Area is measured in square units (cm²); perimeter and circumference in length units (cm).")
            for i in range(0,len(SHAPES),3):
                for col, item in zip(st.columns(3, gap="medium"), SHAPES[i:i+3]):
                    name, symbol, area, perim, meanings, example = item
                    with col:
                        st.markdown(f'<div class="math-card"><h4>{symbol} {name}</h4><div><b>{html.escape(area)}</b></div><div>{html.escape(perim)}</div></div>', unsafe_allow_html=True)
                        if st.button("Explore " + name + " →", key="shape_"+name, use_container_width=True):
                            st.session_state.shape = name
                            st.rerun()
        else:
            name = st.session_state.shape
            _, symbol, area, perim, meanings, example = SHAPE_MAP[name]
            if st.button("← All formulas"):
                st.session_state.shape = None
                st.rerun()
            section_header(f"{symbol} {name}", "Learn the symbols, experiment with measurements, and see an example.")
            with st.container(border=True, key="solid_formula_details"):
                st.markdown("#### Main formulas")
                st.write(f"**Area:** {area}")
                st.write(f"**Perimeter / related formula:** {perim}")
                st.write(f"**What the letters mean:** {meanings}")
                if name == "Triangle":
                    st.caption("Triangle perimeter needs all three side lengths. Base and height only determine area.")
                if name == "Right Triangle":
                    st.caption("P = a + b + c, where c is the hypotenuse.")
                if name == "Regular Polygon":
                    st.caption("The apothem is perpendicular to a side and reaches it from the center.")
            with st.container(border=True, key="solid_formula_explorer"):
                formula_explorer(name, "formula_"+name.replace(" ","_"))
            st.markdown("#### Real-life example")
            st.success(example)
            st.info("Tip: Area measures the space inside a shape. Perimeter measures the distance around its boundary. A height must be perpendicular to the base.")

    elif page == "Practice":
        level = difficulty("Practice")
        if st.session_state.task is None:
            section_header("Practice", "Choose one of 15 problems at your level. Open it for a diagram, hint, and full solution.")
            st.caption(f"{level} · {len(TASKS[level])} problems · Select a card to begin")
            for i, task in enumerate(TASKS[level]):
                title, question, shape, dims, hint, solution, answer = task
                with st.container(border=True, key=f"practice_card_{level}_{i}"):
                    left, right = st.columns([4,1])
                    with left:
                        st.markdown(f"**{i+1:02d}. {title}** · {shape}")
                        st.write(question)
                    with right:
                        if st.button("Open →", key=f"open_{level}_{i}", use_container_width=True):
                            st.session_state.task = i
                            st.rerun()
        else:
            idx = st.session_state.task
            title, question, shape, dims, hint, solution, answer = TASKS[level][idx]
            if st.button("← Back to problems"):
                st.session_state.task = None
                st.rerun()
            section_header(f"Problem {idx+1}: {title}", f"{level} · {shape}")
            with st.container(border=True, key="solid_problem_details"):
                st.markdown("### Your question")
                st.write(question)
                st.caption("The diagram below shows the relevant geometry. Measurements in the question are authoritative; drawings are not to scale.")
            if st.button("📐 Show Diagram", key=f"diag_{level}_{idx}", use_container_width=True):
                st.session_state[f"diagram_{level}_{idx}"] = not st.session_state.get(f"diagram_{level}_{idx}",False)
            if st.session_state.get(f"diagram_{level}_{idx}",False):
                if level == "Advanced":
                    advanced_diagram(idx)
                else:
                    diagram(shape, *dims, color="#16a34a")
            if st.button("💡 Get Hint", key=f"hint_{level}_{idx}", use_container_width=True):
                st.session_state[f"hint_open_{level}_{idx}"] = not st.session_state.get(f"hint_open_{level}_{idx}",False)
            if st.session_state.get(f"hint_open_{level}_{idx}",False):
                st.info(hint)
            if st.button("✅ Show Solution", key=f"solution_{level}_{idx}", use_container_width=True):
                st.session_state[f"solution_open_{level}_{idx}"] = not st.session_state.get(f"solution_open_{level}_{idx}",False)
            if st.session_state.get(f"solution_open_{level}_{idx}",False):
                st.success(f"**Step-by-step solution:** {solution}\n\n**Final answer: {answer}**")
            if st.button("Next problem →", key=f"next_{level}_{idx}"):
                st.session_state.task = (idx+1) % len(TASKS[level])
                st.rerun()

    elif page == "AI Generator":
        section_header("✨ AI Problem Generator", "Your personal geometry challenge, powered by Gemini.")
        with st.container(border=True, key="solid_ai_controls"):
            st.markdown("### 🎯 Customize your challenge")
            level = difficulty("AI Generator")
            topic = st.selectbox("Geometry topic", ["Any topic"] + [s[0] for s in SHAPES], key="ai_topic")
            custom = st.text_area("What would you like to practice? (optional)",
                placeholder="For example: a swimming pool with a path around it, or finding a missing height...",
                max_chars=700, height=95, key="ai_custom_request")
            st.caption("The AI creates a new problem for your selected topic and difficulty. Responses may contain mistakes, so check calculations.")
            pressed = st.button("✨ Generate my problem", key="ai_generate", type="primary", use_container_width=True)
        if pressed:
            with st.spinner("Gemini is generating and independently reviewing your problem (this may take a little longer)..."):
                try:
                    st.session_state.ai_problem = generate_geometry_problem(level, topic, custom)
                    st.session_state.ai_generated_for = (level, topic, custom)
                    st.session_state.ai_show_hint = False
                    st.session_state.ai_show_solution = False
                except (ValueError, RuntimeError) as exc:
                    st.error(str(exc))
        problem = st.session_state.get("ai_problem")
        if problem:
            with st.container(border=True, key="solid_ai_problem"):
                st.markdown("### 📐 " + clean_ai_text(problem["title"]))
                st.caption("AI-generated · " + clean_ai_text(problem["concept"]))
                st.caption("✓ Separate AI math review passed · Not a guarantee of correctness")
                st.write(clean_ai_text(problem["question"]))
            # The original implementation defined render_ai_diagram but never called it.
            with st.expander("📐 Show problem diagram", expanded=False):
                if not render_ai_diagram(problem.get("diagram_spec")):
                    st.info("A reliable diagram was not supplied for this problem. Use the measurements in the question; no missing lengths are assumed.")
                if problem.get("diagram_description") and validate_ai_diagram(problem.get("diagram_spec"))[0]:
                    st.caption(clean_ai_text(problem["diagram_description"]))
            left, right = st.columns(2)
            with left:
                if st.button("💡 " + ("Hide hint" if st.session_state.get("ai_show_hint") else "Get hint"), key="ai_hint", use_container_width=True):
                    st.session_state.ai_show_hint = not st.session_state.get("ai_show_hint", False)
            with right:
                if st.button("✅ " + ("Hide solution" if st.session_state.get("ai_show_solution") else "Show solution"), key="ai_solution", use_container_width=True):
                    st.session_state.ai_show_solution = not st.session_state.get("ai_show_solution", False)
            if st.session_state.get("ai_show_hint"):
                st.info(clean_ai_text(problem["hint"]))
            if st.session_state.get("ai_show_solution"):
                with st.container(border=True, key="solid_ai_solution"):
                    st.markdown("### Step-by-step solution")
                    display_solution_steps(problem["solution"])
                    st.markdown("**Final answer:** " + clean_ai_text(problem["answer"]))
                    with st.expander("Diagram explanation"):
                        st.write(clean_ai_text(problem["diagram_description"]))
            st.caption("A second Gemini call checks mathematical consistency and solvability. AI review can still miss errors; verify important answers independently.")
        elif not get_gemini_key():
            st.info("🔑 Gemini is not configured yet. Add GEMINI_API_KEY to `.streamlit/secrets.toml` locally, or to your Streamlit Cloud app secrets after deployment.")
