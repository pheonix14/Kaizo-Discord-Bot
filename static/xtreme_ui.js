/**
 * XTREME UI ENGINE v3 — NEW ERA
 * 100% based on refrence.html design system.
 * Zero conflicts. Zero overlaps. Clean separation of layers.
 *
 * LAYER ORDER (z-index):
 *   0  — bg-wrap (background image)
 *   1  — grain + color-bleed
 *   2  — vignette
 *   3  — watermark
 *   4  — fbf animation (background layer, subtle)
 *  10  — page content (main, sections)
 *  20  — scroll counter, slide dots, marquee
 * 100  — nav
 * 150  — fullscreen menu overlay
 * 200  — cursor
 * 999  — notification toast
 * 9000 — page loader
 */

(function () {
  'use strict';

  /* ══════════════════════════════════════════
     CONFIG
  ══════════════════════════════════════════ */
  const BG_COUNT    = 900;
  const BG_INTERVAL = 10000;   // 10 sec between bg changes
  const WM_INTERVAL = 8000;    // 8 sec between watermark font changes
  const FPS         = 8;       // frame-by-frame animation FPS
  const SEED        = Math.floor(Math.random() * BG_COUNT) + 1;

  const PALETTES = [
    { c1: '#ff2d55', c2: '#0affe4' },
    { c1: '#ff6b35', c2: '#c7ff3a' },
    { c1: '#a855f7', c2: '#22d3ee' },
    { c1: '#f59e0b', c2: '#f43f5e' },
    { c1: '#10b981', c2: '#6366f1' },
    { c1: '#ec4899', c2: '#fbbf24' },
    { c1: '#e11d48', c2: '#818cf8' },
    { c1: '#14b8a6', c2: '#fb923c' },
    { c1: '#8b5cf6', c2: '#34d399' },
    { c1: '#f97316', c2: '#60a5fa' },
  ];

  const WM_FONTS = [
    "'Bebas Neue', sans-serif",
    "'Orbitron', sans-serif",
    "'Dancing Script', cursive",
    "'Playfair Display', serif",
    "'Cinzel Decorative', serif",
    "'Monoton', cursive",
    "'Black Han Sans', sans-serif",
    "'Permanent Marker', cursive",
    "'Abril Fatface', serif",
    "'Righteous', sans-serif",
  ];

  const WM_SIZES = ['10vw', '13vw', '16vw', '20vw', '8vw', '18vw'];

  const NAV_ITEMS = [
    { sym: '◈', label: 'Home',    href: '/' },
    { sym: '◉', label: 'Tokens',  href: '/config' },
    { sym: '◫', label: 'Dex',     href: '/dex' },
    { sym: '◎', label: 'History', href: '/history' },
    { sym: '⬡', label: 'OwO',     href: '/owo' },
    { sym: '◐', label: 'Slash',   href: '/slash' },
    { sym: '⊕', label: 'Spam',    href: '/spam' },
    { sym: '◆', label: 'Msg',     href: '/msg' },
    { sym: '⌘', label: 'Mimic',   href: '/mimic' },
    { sym: '◈', label: 'Image',   href: '/image' },
    { sym: '◉', label: 'Hook',    href: '/hook' },
    { sym: '◎', label: 'Test',    href: '/test' },
    { sym: '⊞', label: 'Captcha', href: '/captcha' },
    { sym: '⬡', label: 'Balance', href: '/bal' },
    { sym: '◆', label: 'Data',    href: '/data' },
  ];

  const NOTIF_MSGS = [
    { t: '◈ XTREME — New Era',  b: 'Every refresh is a new world. Welcome back.' },
    { t: '⬡ System Online',     b: 'All nodes are active and catching.' },
    { t: '◉ Status Report',     b: 'Check your node dashboard for live updates.' },
    { t: '◎ XTREME Alert',      b: 'New activity detected on your nodes.' },
    { t: '◆ Engine Running',    b: 'Fafnir engine running at peak capacity.' },
  ];

  const MQ_ITEMS = [
    'XTREME','◈','New Era','⬡','Motion','◎','Design','◉',
    'Nodes','◆','Frame','⊕','Visual','◐','System','⌘','Drop'
  ];

  /* ══════════════════════════════════════════
     STATE
  ══════════════════════════════════════════ */
  let bgIdx       = SEED;
  let palIdx      = Math.floor(Math.random() * PALETTES.length);
  let wmFontIdx   = Math.floor(Math.random() * WM_FONTS.length);
  let wmSizeIdx   = Math.floor(Math.random() * WM_SIZES.length);
  let fbfIdx      = 0;
  let menuOpen    = false;
  let initialized = false;

  /* ══════════════════════════════════════════
     GOOGLE FONTS
  ══════════════════════════════════════════ */
  function injectFonts() {
    if (document.getElementById('x3-fonts')) return;
    const pre1 = document.createElement('link');
    pre1.rel = 'preconnect'; pre1.href = 'https://fonts.googleapis.com';
    document.head.appendChild(pre1);
    const pre2 = document.createElement('link');
    pre2.rel = 'preconnect'; pre2.href = 'https://fonts.gstatic.com'; pre2.crossOrigin = '';
    document.head.appendChild(pre2);
    const link1 = document.createElement('link');
    link1.id = 'x3-fonts-base'; link1.rel = 'stylesheet';
    link1.href = 'https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Space+Grotesk:wght@300;400;500;700&family=Orbitron:wght@900&display=swap';
    document.head.appendChild(link1);

    const link2 = document.createElement('link');
    link2.id = 'x3-fonts-wm'; link2.rel = 'stylesheet';
    // Highly optimized font subset just for the watermark text "XTREME"
    link2.href = 'https://fonts.googleapis.com/css2?family=Dancing+Script:wght@700&family=Playfair+Display:ital,wght@0,900;1,400&family=Abril+Fatface&family=Righteous&family=Permanent+Marker&family=Black+Han+Sans&family=Cinzel+Decorative:wght@900&family=Monoton&display=swap&text=XTREME';
    document.head.appendChild(link2);
  }

  /* ══════════════════════════════════════════
     CSS — everything in one <style> block
  ══════════════════════════════════════════ */
  function injectCSS() {
    if (document.getElementById('x3-css')) return;
    const s = document.createElement('style');
    s.id = 'x3-css';
    s.textContent = `
/* ═══ XTREME UI v3 ═══ */
:root {
  --xc1: #ff2d55;
  --xc2: #0affe4;
  --nav-h: 72px;
}

/* ── RESET ADDITIONS ── */
*, *::before, *::after { box-sizing: border-box; }
html { scroll-behavior: smooth; }
body {
  margin: 0;
  background: #000 !important;
  color: #fff !important;
  min-height: 100vh;
  overflow-x: hidden;
  font-family: 'Space Grotesk', -apple-system, sans-serif !important;
}

/* ── PAGE LOADER (z:9000) ── */
#x3-loader {
  position: fixed; inset: 0; z-index: 9000;
  background: #000;
  display: flex; flex-direction: column;
  align-items: center; justify-content: center; gap: 24px;
  transition: opacity .6s .2s, visibility .6s .2s;
}
#x3-loader.done { opacity: 0; visibility: hidden; pointer-events: none; }
#x3-loader-word {
  font-family: 'Bebas Neue', sans-serif;
  font-size: clamp(40px, 8vw, 80px);
  letter-spacing: .2em; color: #fff;
  animation: x3LoadPulse 1.2s ease-in-out infinite;
}
@keyframes x3LoadPulse { 0%,100%{opacity:1} 50%{opacity:.25} }
#x3-loader-bar-outer { width: 200px; height: 2px; background: rgba(255,255,255,.1); }
#x3-loader-bar-inner { height: 100%; background: var(--xc1); width: 0; animation: x3LoadFill 1.6s ease forwards; }
@keyframes x3LoadFill { 0%{width:0} 100%{width:100%} }

/* ── BG WRAP (z:0) ── */
#x3-bg-wrap {
  position: fixed; inset: 0; z-index: 0; overflow: hidden;
}
#x3-bg-img {
  position: absolute; inset: -10%;
  width: 120%; height: 120%;
  object-fit: cover;
  filter: brightness(.45) saturate(1.3) contrast(1.05);
  transition: opacity 1.2s ease;
}
#x3-bg-img.xfade-out { opacity: 0; }
#x3-bg-img.xfade-in  { opacity: 1; }

/* ── GRAIN (z:1) ── */
#x3-grain {
  position: fixed; inset: 0; z-index: 1; pointer-events: none;
  background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)' opacity='.06'/%3E%3C/svg%3E");
  opacity: .4;
}

/* ── COLOR BLEED (z:1) ── */
#x3-color-bleed {
  position: fixed; inset: 0; z-index: 1; pointer-events: none;
  mix-blend-mode: color; opacity: .25;
  transition: background 2s ease;
}

/* ── VIGNETTE (z:2) ── */
#x3-vignette {
  position: fixed; inset: 0; z-index: 2; pointer-events: none;
  background: radial-gradient(ellipse at center, transparent 30%, rgba(0,0,0,.72) 100%);
}

/* ── WATERMARK (z:3) ── */
#x3-wm {
  position: fixed; top: 50%; left: 50%;
  transform: translate(-50%, -50%);
  z-index: 3; pointer-events: none;
  white-space: nowrap; user-select: none;
  opacity: .06; color: #fff; line-height: 1; letter-spacing: .05em;
  transition: font-family .5s, font-size .5s;
  animation: x3WmPulse 8s ease-in-out infinite;
}
@keyframes x3WmPulse {
  0%,100% { opacity:.05; transform:translate(-50%,-50%) scale(1); }
  50%      { opacity:.10; transform:translate(-50%,-50%) scale(1.02); }
}

/* ── FBF STAGE (z:4, behind content) ── */
#x3-fbf {
  position: fixed; inset: 0; z-index: 4; pointer-events: none;
  display: flex; align-items: center; justify-content: center;
  opacity: .5;
}
.x3-fbf-canvas {
  position: relative;
  width: min(520px, 88vw); height: min(520px, 88vw);
  display: flex; align-items: center; justify-content: center;
}
.x3-fbf-frame {
  position: absolute; inset: 0;
  display: flex; align-items: center; justify-content: center;
  opacity: 0; transition: opacity .05s;
}
.x3-fbf-frame.visible { opacity: 1; }
.x3-fbf-shape { border-radius: 0; }
.x3-f1 .x3-fbf-shape { width:40%;height:40%; background:var(--xc1); }
.x3-f2 .x3-fbf-shape { width:55%;height:20%; background:var(--xc2); transform:rotate(45deg); }
.x3-f3 .x3-fbf-shape { width:70%;height:70%; background:none; border:3px solid #fff; border-radius:50%; }
.x3-f4 .x3-fbf-shape { width:30%;height:80%; background:var(--xc1); transform:skewX(-15deg); }
.x3-f5 .x3-fbf-shape { width:80%;height:80%; background:none; border:3px solid var(--xc2); transform:rotate(45deg); }
.x3-f6 .x3-fbf-shape { width:50%;height:50%; background:#fff; clip-path:polygon(50% 0%,100% 100%,0% 100%); }
.x3-f7 .x3-fbf-shape { width:60%;height:60%; background:none; border:2px solid var(--xc1); border-radius:50%;
  box-shadow:0 0 0 20px rgba(255,45,85,.08),0 0 0 44px rgba(255,45,85,.04); }
.x3-f8 .x3-fbf-shape { width:45%;height:45%; background:var(--xc2); transform:rotate(22.5deg); }
.x3-fbf-word {
  position: absolute;
  font-family: 'Bebas Neue', sans-serif;
  font-size: clamp(72px, 16vw, 160px);
  color: rgba(255,255,255,.05); letter-spacing: .1em;
  pointer-events: none; white-space: nowrap;
}
@media (max-width: 768px) { #x3-fbf { opacity: .25; } }

/* ── NAV (z:100) ── */
#x3-nav {
  position: fixed; top: 0; left: 0; right: 0;
  height: var(--nav-h); z-index: 100;
  display: flex; align-items: center; justify-content: space-between;
  padding: 0 clamp(20px, 4vw, 48px);
  background: linear-gradient(to bottom, rgba(0,0,0,.6), transparent);
  backdrop-filter: blur(0px);
  transition: background .4s, backdrop-filter .4s;
}
#x3-nav.x3-scrolled {
  background: rgba(0,0,0,.88) !important;
  backdrop-filter: blur(22px) !important;
}

/* Logo */
#x3-logo {
  font-family: 'Bebas Neue', sans-serif;
  font-size: clamp(22px, 2.8vw, 30px);
  letter-spacing: .12em; color: #fff;
  text-decoration: none; position: relative;
  flex-shrink: 0;
}
#x3-logo::after {
  content: ''; position: absolute; bottom: -2px; left: 0;
  width: 0; height: 2px; background: var(--xc1);
  transition: width .4s;
}
#x3-logo:hover::after { width: 100%; }

/* Desktop links */
#x3-nav-links {
  display: flex; align-items: center;
  gap: clamp(16px, 2vw, 32px);
  list-style: none; margin: 0; padding: 0;
}
#x3-nav-links a {
  color: rgba(255,255,255,.72);
  text-decoration: none;
  font-family: 'Space Grotesk', sans-serif;
  font-size: 12px; letter-spacing: .12em; text-transform: uppercase;
  transition: color .2s; position: relative;
  display: flex; align-items: center; gap: 5px;
}
#x3-nav-links a::before {
  content: attr(data-sym);
  color: var(--xc1); opacity: .6; font-size: 10px;
  transition: opacity .2s;
}
#x3-nav-links a:hover { color: #fff; }
#x3-nav-links a:hover::before { opacity: 1; }
#x3-nav-links a.x3-active { color: #fff; }
#x3-nav-links a.x3-active::before { opacity: 1; }

/* Nav right */
#x3-nav-right { display: flex; align-items: center; gap: 14px; flex-shrink: 0; }

/* Bell */
#x3-bell {
  background: none; border: 1.5px solid rgba(255,255,255,.25);
  color: #fff; width: 40px; height: 40px; border-radius: 50%;
  cursor: none; display: flex; align-items: center; justify-content: center;
  font-size: 17px; position: relative;
  transition: border-color .2s, background .2s;
  flex-shrink: 0;
}
#x3-bell:hover { border-color: var(--xc1); background: rgba(255,45,85,.15); }
#x3-bell-dot {
  position: absolute; top: 7px; right: 8px;
  width: 7px; height: 7px; border-radius: 50%;
  background: var(--xc1); box-shadow: 0 0 8px var(--xc1);
  animation: x3DotPulse 2s infinite;
}
@keyframes x3DotPulse { 0%,100%{transform:scale(1)} 50%{transform:scale(1.45)} }

/* Hamburger */
#x3-ham {
  width: 44px; height: 44px;
  background: none; border: 1.5px solid rgba(255,255,255,.25);
  border-radius: 4px; cursor: none;
  display: flex; flex-direction: column;
  align-items: center; justify-content: center; gap: 5px;
  transition: border-color .2s; position: relative; z-index: 200;
  flex-shrink: 0;
}
#x3-ham:hover { border-color: var(--xc1); }
#x3-ham span {
  display: block; width: 20px; height: 1.5px; background: #fff;
  transition: all .35s cubic-bezier(.23,1,.32,1); transform-origin: center;
}
#x3-ham.open span:nth-child(1) { transform: translateY(6.5px) rotate(45deg); }
#x3-ham.open span:nth-child(2) { opacity: 0; transform: scaleX(0); }
#x3-ham.open span:nth-child(3) { transform: translateY(-6.5px) rotate(-45deg); }

/* ── FULLSCREEN MENU (z:150) ── */
#x3-menu {
  position: fixed; inset: 0; z-index: 150;
  background: rgba(0,0,0,.97);
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  opacity: 0; pointer-events: none;
  transition: opacity .45s cubic-bezier(.23,1,.32,1);
  backdrop-filter: blur(24px);
  overflow: hidden;
  padding: 14px;
}
#x3-menu.open { opacity: 1; pointer-events: all; }
#x3-menu-inner {
  text-align: center;
  width: 100%;
  max-width: 400px;
  margin: auto;
  padding: 24px 0;
  overflow-y: auto !important;
  max-height: 85vh !important;
  -webkit-overflow-scrolling: touch;
}
#x3-menu-tag {
  font-family: 'Space Grotesk', sans-serif;
  font-size: 6px; letter-spacing: .3em; color: var(--xc1);
  text-transform: uppercase; margin-bottom: 10px;
  animation: x3FadeUp .4s .1s both;
}
#x3-menu-nav { list-style: none; padding: 0; margin: 0; }
#x3-menu-nav li { overflow: hidden; animation: x3FadeUp .5s both; }
#x3-menu-nav li:nth-child(1)  { animation-delay: .12s; }
#x3-menu-nav li:nth-child(2)  { animation-delay: .17s; }
#x3-menu-nav li:nth-child(3)  { animation-delay: .22s; }
#x3-menu-nav li:nth-child(4)  { animation-delay: .27s; }
#x3-menu-nav li:nth-child(5)  { animation-delay: .32s; }
#x3-menu-nav li:nth-child(6)  { animation-delay: .37s; }
#x3-menu-nav li:nth-child(7)  { animation-delay: .42s; }
#x3-menu-nav li:nth-child(8)  { animation-delay: .47s; }
#x3-menu-nav li:nth-child(9)  { animation-delay: .52s; }
#x3-menu-nav li:nth-child(10) { animation-delay: .57s; }
#x3-menu-nav li:nth-child(11) { animation-delay: .62s; }
#x3-menu-nav li:nth-child(12) { animation-delay: .67s; }
#x3-menu-nav li:nth-child(13) { animation-delay: .72s; }
#x3-menu-nav li:nth-child(14) { animation-delay: .77s; }
#x3-menu-nav a {
  font-family: 'Bebas Neue', sans-serif;
  font-size: clamp(13px, 2.1vw, 27px);
  color: rgba(255,255,255,.15); text-decoration: none;
  letter-spacing: .07em;
  display: inline-flex; align-items: center; justify-content: center; gap: 9px;
  line-height: 1.1;
  transition: color .3s, transform .3s;
}
#x3-menu-nav a .x3-msym {
  font-family: 'Space Grotesk', sans-serif;
  font-size: clamp(7px, 1vw, 9px); color: var(--xc1);
  opacity: 0; transform: translateX(-20px);
  transition: opacity .3s, transform .3s;
}
#x3-menu-nav a:hover { color: #fff; transform: translateX(12px); }
#x3-menu-nav a:hover .x3-msym { opacity: 1; transform: translateX(0); }
#x3-menu-nav a.x3-cur { color: rgba(255,255,255,.5); }
#x3-menu-close {
  position: absolute; top: 14px; right: 14px;
  width: 25px; height: 25px; border-radius: 50%;
  border: 1.5px solid var(--xc1);
  background: rgba(255,45,85,.1); color: var(--xc1);
  font-size: 13px; display: flex; align-items: center; justify-content: center;
  cursor: pointer; z-index: 220; transition: all .25s ease;
  box-shadow: 0 0 10px rgba(255,45,85,.3);
}
#x3-menu-close:hover {
  border-color: #fff;
  background: rgba(255,255,255,.1);
  color: #fff;
  box-shadow: 0 0 15px rgba(255,255,255,.5);
  transform: rotate(90deg);
}
#x3-menu-status {
  display: flex; align-items: center; gap: 5px; justify-content: center;
  margin-top: 11px;
  font-family: 'Space Grotesk', sans-serif;
  font-size: 6px; letter-spacing: .18em; text-transform: uppercase;
  color: rgba(255,255,255,.3); animation: x3FadeUp .5s .8s both;
}
#x3-menu-dot { width: 6px; height: 6px; border-radius: 50%; background: #22c55e; animation: x3DotPulse 2s infinite; }
@keyframes x3FadeUp { from{opacity:0;transform:translateY(28px)} to{opacity:1;transform:translateY(0)} }

/* ── SCROLL COUNTER (z:20) ── */
#x3-scroll-pct {
  position: fixed; bottom: 36px; right: 40px; z-index: 20;
  font-family: 'Space Grotesk', sans-serif;
  font-size: 11px; letter-spacing: .15em; color: rgba(255,255,255,.4);
  writing-mode: vertical-rl; display: flex; align-items: center; gap: 8px;
  pointer-events: none;
}
#x3-scroll-pct span { color: #fff; font-weight: 700; font-size: 14px; }

/* ── SLIDE DOTS (z:20) ── */
#x3-slide-dots {
  position: fixed; right: 40px; top: 50%;
  transform: translateY(-50%); z-index: 20;
  display: flex; flex-direction: column; gap: 8px;
}
.x3-slide-dot {
  width: 3px; height: 20px;
  background: rgba(255,255,255,.2); border-radius: 2px;
  transition: height .3s, background .3s;
}
.x3-slide-dot.x3-active { height: 36px; background: #fff; }

/* ── NOTIFICATION TOAST (z:999) ── */
#x3-toast {
  position: fixed; top: calc(var(--nav-h) + 14px); right: 24px; z-index: 999;
  background: rgba(10,10,10,.96);
  border: 1px solid rgba(255,255,255,.12);
  border-left: 3px solid var(--xc1);
  padding: 16px 20px;
  width: min(300px, calc(100vw - 48px));
  backdrop-filter: blur(20px);
  transform: translateX(120%);
  transition: transform .4s cubic-bezier(.23,1,.32,1);
}
#x3-toast.show { transform: translateX(0); }
#x3-toast-title { font-family:'Space Grotesk',sans-serif; font-size:13px; font-weight:700; color:#fff; letter-spacing:.05em; margin-bottom:4px; }
#x3-toast-body  { font-family:'Space Grotesk',sans-serif; font-size:12px; color:rgba(255,255,255,.5); line-height:1.5; }
#x3-toast-close {
  position: absolute; top: 10px; right: 12px;
  background: none; border: none; color: rgba(255,255,255,.3);
  cursor: pointer; font-size: 15px; line-height: 1; transition: color .2s;
}
#x3-toast-close:hover { color: #fff; }

/* ── CONTENT LAYER — ensure main content sits above bg but below nav ── */
body > main,
body > .main-content,
body > section:not(#x3-loader):not(#x3-fbf),
body > div.flex-1,
body > div:not([id^="x3-"]):not(#bg-overlay):not(.bg-overlay) {
  position: relative;
  z-index: 10;
}

/* ── BODY LAYOUT ── */
body.x3-ready {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
}
body.x3-ready > main,
body.x3-ready > .flex-1 {
  flex: 1;
  padding-top: var(--nav-h);
  position: relative; z-index: 10;
}

/* ── HIDE LEGACY BG OVERLAYS ── */
#bg-overlay,
.bg-overlay { display: none !important; }

/* ── GLASS CARDS ── */
.glass {
  background: rgba(6,6,6,.55) !important;
  backdrop-filter: blur(26px) saturate(1.15) !important;
  -webkit-backdrop-filter: blur(26px) saturate(1.15) !important;
  border: 1px solid rgba(255,255,255,.1) !important;
  box-shadow: 0 8px 40px rgba(0,0,0,.5), inset 0 1px 0 rgba(255,255,255,.07) !important;
  position: relative; overflow: hidden;
}
.glass::before {
  content: ''; position: absolute; inset: 0;
  background: linear-gradient(135deg, rgba(255,255,255,.035) 0%, transparent 65%);
  pointer-events: none; z-index: 0;
}
.glass > * { position: relative; z-index: 1; }
.glass:hover {
  border-color: rgba(255,255,255,.16) !important;
  box-shadow: 0 14px 52px rgba(0,0,0,.65), inset 0 1px 0 rgba(255,255,255,.1) !important;
  transform: translateY(-1px);
}

/* ── TYPOGRAPHY ── */
h1 { font-family: 'Bebas Neue', sans-serif !important; letter-spacing: .06em !important; line-height: .92 !important; }
h2 { font-family: 'Space Grotesk', sans-serif !important; font-weight: 700 !important; letter-spacing: .04em !important; }
h3, h4 { font-family: 'Space Grotesk', sans-serif !important; font-weight: 700 !important; }
.stat-value { font-family: 'Bebas Neue', sans-serif !important; font-weight: 900 !important; }
.mono, code { font-family: 'Courier New', monospace !important; }

/* ── BUTTONS ── */
button {
  font-family: 'Space Grotesk', sans-serif !important;
  font-weight: 700 !important; letter-spacing: .08em !important;
  transition: all .28s cubic-bezier(.23,1,.32,1) !important;
}
button:not(#x3-ham):not(#x3-bell):not(#x3-toast-close):active { transform: scale(.96) !important; }

/* ── INPUTS ── */
input[type="text"], input[type="number"], input[type="email"],
input[type="password"], input[type="url"], textarea, select {
  font-family: 'Space Grotesk', sans-serif !important;
  background: rgba(0,0,0,.55) !important;
  border: 1px solid rgba(255,255,255,.1) !important;
  color: #fff !important; border-radius: 12px !important;
  padding: 10px 16px !important; outline: none !important;
  transition: border-color .2s, box-shadow .2s !important;
  width: 100%;
}
input:focus, input[type="number"]:focus, textarea:focus, select:focus {
  border-color: var(--xc1) !important;
  box-shadow: 0 0 0 3px rgba(255,45,85,.18) !important;
}
input::placeholder, textarea::placeholder { color: rgba(255,255,255,.28) !important; }
input[type="range"] {
  background: transparent !important; border: none !important;
  padding: 0 !important; accent-color: var(--xc1) !important;
}

/* ── TOGGLE SWITCHES ── */
.toggle-checkbox:checked + .toggle-label {
  background: var(--xc1) !important;
  box-shadow: 0 0 12px rgba(255,45,85,.4) !important;
}

/* ── SCROLLBARS ── */
::-webkit-scrollbar { width: 2px; height: 2px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: var(--xc1); border-radius: 2px; }

/* ── LOG ENTRIES ── */
[id*="logs"] > div { font-family: 'Courier New', monospace !important; font-size: 11px !important; border-radius: 8px !important; }

/* ── NOTIFICATION DROPDOWN ── */
#x3-notif-dropdown {
  position: absolute;
  top: 60px;
  right: 64px;
  width: 340px;
  max-height: 480px;
  background: rgba(10,10,10,0.85);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border: 1px solid rgba(255,255,255,0.08);
  border-radius: 12px;
  box-shadow: 0 10px 30px rgba(0,0,0,0.8), inset 0 1px 0 rgba(255,255,255,0.05);
  z-index: 1000;
  display: none;
  flex-direction: column;
  overflow: hidden;
  animation: x3FadeUp 0.3s cubic-bezier(0.23, 1, 0.32, 1);
}
#x3-notif-dropdown.open {
  display: flex;
}
#x3-notif-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  border-bottom: 1px solid rgba(255,255,255,0.08);
  background: rgba(0,0,0,0.2);
}
#x3-notif-header h4 {
  margin: 0;
  font-family: 'Space Grotesk', sans-serif;
  font-size: 13px;
  font-weight: 700;
  letter-spacing: 0.05em;
  color: #fff;
  text-transform: uppercase;
}
#x3-notif-mark-read {
  background: none;
  border: none;
  color: var(--xc1);
  font-family: 'Space Grotesk', sans-serif;
  font-size: 11px;
  font-weight: 700;
  cursor: pointer;
  padding: 4px 8px;
  border-radius: 4px;
  transition: background 0.2s, color 0.2s;
  letter-spacing: 0.05em;
  text-transform: uppercase;
}
#x3-notif-mark-read:hover {
  background: rgba(255,45,85,0.15);
  color: #fff;
}
#x3-notif-list {
  flex: 1;
  overflow-y: auto !important;
  padding: 8px 0;
  display: flex;
  flex-direction: column;
  max-height: 400px;
}
.x3-notif-item {
  display: flex;
  gap: 12px;
  padding: 12px 16px;
  border-bottom: 1px solid rgba(255,255,255,0.03);
  transition: background 0.2s;
  position: relative;
}
.x3-notif-item:last-child {
  border-bottom: none;
}
.x3-notif-item:hover {
  background: rgba(255,255,255,0.03);
}
.x3-notif-item.unread {
  background: rgba(255,45,85,0.04);
}
.x3-notif-item.unread::before {
  content: '';
  position: absolute;
  left: 6px;
  top: 50%;
  transform: translateY(-50%);
  width: 4px;
  height: 4px;
  border-radius: 50%;
  background: var(--xc1);
}
.x3-notif-icon {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  flex-shrink: 0;
}
.x3-notif-icon.success {
  background: rgba(34,197,94,0.15);
  color: #22c55e;
  border: 1px solid rgba(34,197,94,0.25);
}
.x3-notif-icon.error {
  background: rgba(239,68,68,0.15);
  color: #ef4444;
  border: 1px solid rgba(239,68,68,0.25);
}
.x3-notif-icon.info {
  background: rgba(59,130,246,0.15);
  color: #3b82f6;
  border: 1px solid rgba(59,130,246,0.25);
}
.x3-notif-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.x3-notif-title {
  font-family: 'Space Grotesk', sans-serif;
  font-size: 12px;
  font-weight: 700;
  color: #fff;
}
.x3-notif-desc {
  font-family: 'Space Grotesk', sans-serif;
  font-size: 11px;
  color: rgba(255,255,255,0.6);
  line-height: 1.4;
}
.x3-notif-time {
  font-family: 'Space Grotesk', sans-serif;
  font-size: 9px;
  color: rgba(255,255,255,0.3);
  margin-top: 4px;
}
.x3-notif-empty {
  padding: 24px;
  text-align: center;
  color: rgba(255,255,255,0.4);
  font-family: 'Space Grotesk', sans-serif;
  font-size: 12px;
}

/* ── MOBILE ── */
@media (max-width: 768px) {
  #x3-nav-links { display: none !important; }
  #x3-scroll-pct, #x3-slide-dots { display: none; }
  body.x3-ready > main,
  body.x3-ready > .flex-1 {
    padding-top: calc(var(--nav-h) + 8px);
    padding-bottom: 24px;
  }
  #x3-menu-nav a {
    font-size: 12px !important;
    line-height: 1.3 !important;
  }
  #x3-menu-nav a .x3-msym {
    font-size: 7px !important;
  }
  #x3-menu-tag {
    margin-bottom: 6px !important;
  }
  #x3-menu-status {
    margin-top: 8px !important;
  }
  #x3-menu-close {
    top: 9px; right: 9px;
    width: 22px; height: 22px;
    font-size: 10px;
    cursor: pointer !important;
  }
  #x3-notif-dropdown {
    right: 14px;
    width: calc(100vw - 28px);
    max-height: 380px;
  }
}
@media (min-width: 769px) {
  body.x3-ready > main,
  body.x3-ready > .flex-1 {
    padding-bottom: 24px;
  }
}

/* ── PAGE FADE-IN ANIMATION ── */
body { opacity: 0; transition: opacity .5s ease; }
body.x3-visible { opacity: 1; }

/* ── CONTENT ENTRY ANIMATIONS ── */
@keyframes x3SlideUp {
  from { opacity: 0; transform: translateY(20px); }
  to   { opacity: 1; transform: translateY(0); }
}
`;
    document.head.appendChild(s);
  }

  /* ══════════════════════════════════════════
     BUILD SHELL — inject all XUI DOM elements
  ══════════════════════════════════════════ */
  function buildShell() {

    /* Page Loader */
    if (!document.getElementById('x3-loader')) {
      const el = document.createElement('div');
      el.id = 'x3-loader';
      el.innerHTML = `<div id="x3-loader-word">XTREME</div><div id="x3-loader-bar-outer"><div id="x3-loader-bar-inner"></div></div>`;
      document.body.insertBefore(el, document.body.firstChild);
    }

    /* BG Wrap */
    if (!document.getElementById('x3-bg-wrap')) {
      const wrap = document.createElement('div'); wrap.id = 'x3-bg-wrap';
      wrap.innerHTML = `<img id="x3-bg-img" src="" alt="">`;
      document.body.insertBefore(wrap, document.getElementById('x3-loader').nextSibling);
    }

    /* Grain, Color Bleed, Vignette */
    const layers = [
      { id: 'x3-grain',       tag: 'div' },
      { id: 'x3-color-bleed', tag: 'div' },
      { id: 'x3-vignette',    tag: 'div' },
    ];
    layers.forEach(({ id, tag }) => {
      if (!document.getElementById(id)) {
        const el = document.createElement(tag); el.id = id;
        document.body.appendChild(el);
      }
    });

    /* Watermark */
    if (!document.getElementById('x3-wm')) {
      const wm = document.createElement('div'); wm.id = 'x3-wm'; wm.textContent = 'XTREME';
      document.body.appendChild(wm);
    }

    /* FBF */
    if (!document.getElementById('x3-fbf')) {
      const fbf = document.createElement('div'); fbf.id = 'x3-fbf';
      fbf.innerHTML = `
        <div class="x3-fbf-canvas">
          <div class="x3-fbf-word">XTREME</div>
          <div class="x3-fbf-frame x3-f1 visible"><div class="x3-fbf-shape"></div></div>
          <div class="x3-fbf-frame x3-f2"><div class="x3-fbf-shape"></div></div>
          <div class="x3-fbf-frame x3-f3"><div class="x3-fbf-shape"></div></div>
          <div class="x3-fbf-frame x3-f4"><div class="x3-fbf-shape"></div></div>
          <div class="x3-fbf-frame x3-f5"><div class="x3-fbf-shape"></div></div>
          <div class="x3-fbf-frame x3-f6"><div class="x3-fbf-shape"></div></div>
          <div class="x3-fbf-frame x3-f7"><div class="x3-fbf-shape"></div></div>
          <div class="x3-fbf-frame x3-f8"><div class="x3-fbf-shape"></div></div>
        </div>`;
      document.body.appendChild(fbf);
    }

    /* Toast */
    if (!document.getElementById('x3-toast')) {
      const toast = document.createElement('div'); toast.id = 'x3-toast';
      toast.innerHTML = `
        <button id="x3-toast-close" onclick="window.XUI.closeToast()">✕</button>
        <div id="x3-toast-title">XTREME</div>
        <div id="x3-toast-body">Welcome to the new era.</div>`;
      document.body.appendChild(toast);
    }

    /* Scroll percent */
    if (!document.getElementById('x3-scroll-pct')) {
      const sp = document.createElement('div'); sp.id = 'x3-scroll-pct';
      sp.innerHTML = `<span id="x3-pct">00</span>%`;
      document.body.appendChild(sp);
    }

    /* Slide dots */
    if (!document.getElementById('x3-slide-dots')) {
      const dots = document.createElement('div'); dots.id = 'x3-slide-dots';
      dots.innerHTML = [0,1,2,3].map((_, i) => `<div class="x3-slide-dot${i===0?' x3-active':''}"></div>`).join('');
      document.body.appendChild(dots);
    }

    /* Mark body ready */
    document.body.classList.add('x3-ready');
  }

  /* ══════════════════════════════════════════
     NAV — remove old, build new
  ══════════════════════════════════════════ */
  function buildNav() {
    /* remove ALL old navs from HTML */
    document.querySelectorAll('nav:not(#x3-nav)').forEach(n => n.remove());

    if (document.getElementById('x3-nav')) return;

    const path = window.location.pathname;
    const navEl = document.createElement('nav');
    navEl.id = 'x3-nav';

    /* Logo */
    const logo = document.createElement('a');
    logo.id = 'x3-logo'; logo.href = '/'; logo.textContent = 'XTREME';
    navEl.appendChild(logo);

    /* Desktop links */
    const ul = document.createElement('ul'); ul.id = 'x3-nav-links';
    NAV_ITEMS.forEach(item => {
      const li = document.createElement('li');
      const a  = document.createElement('a');
      a.href = item.href;
      a.setAttribute('data-sym', item.sym);
      a.textContent = item.label;
      const isActive = path === item.href || (item.href !== '/' && path.startsWith(item.href));
      if (isActive) a.classList.add('x3-active');
      li.appendChild(a); ul.appendChild(li);
    });
    navEl.appendChild(ul);

    /* Right cluster */
    const right = document.createElement('div'); right.id = 'x3-nav-right';
    right.style.position = 'relative';

    /* Bell */
    const bell = document.createElement('button'); bell.id = 'x3-bell'; bell.title = 'Notifications';
    bell.innerHTML = `◉<div id="x3-bell-dot" style="display: none;"></div>`;
    bell.onclick = (e) => { e.stopPropagation(); window.XUI.toggleNotifDropdown(); };
    right.appendChild(bell);

    /* Dropdown */
    const notifDropdown = document.createElement('div');
    notifDropdown.id = 'x3-notif-dropdown';
    notifDropdown.onclick = (e) => e.stopPropagation();
    notifDropdown.innerHTML = `
      <div id="x3-notif-header">
        <h4>Notifications</h4>
        <button id="x3-notif-mark-read" onclick="window.XUI.markAllNotificationsRead()">Mark all read</button>
      </div>
      <div id="x3-notif-list">
        <div class="x3-notif-empty">No notifications</div>
      </div>
    `;
    right.appendChild(notifDropdown);

    /* Ham */
    const ham = document.createElement('button'); ham.id = 'x3-ham'; ham.setAttribute('aria-label','Menu');
    ham.innerHTML = `<span></span><span></span><span></span>`;
    ham.onclick = () => window.XUI.toggleMenu();
    right.appendChild(ham);

    navEl.appendChild(right);

    /* prepend nav — it must be first visible item */
    document.body.insertBefore(navEl, document.getElementById('x3-toast') || document.body.firstChild);

    /* fullscreen menu */
    if (!document.getElementById('x3-menu')) {
      const menu = document.createElement('div'); menu.id = 'x3-menu';
      const items = NAV_ITEMS.map(item => {
        const cur = path === item.href;
        return `<li><a href="${item.href}" onclick="window.XUI.closeMenu()" class="${cur?'x3-cur':''}"><span class="x3-msym">${item.sym}</span>${item.label}</a></li>`;
      }).join('');
      menu.innerHTML = `
        <button id="x3-menu-close" onclick="window.XUI.closeMenu()" aria-label="Close Menu">✕</button>
        <div id="x3-menu-inner">
          <p id="x3-menu-tag">◈ Navigation ◈</p>
          <ul id="x3-menu-nav">${items}</ul>
          <div id="x3-menu-status"><span id="x3-menu-dot"></span>XTREME ENGINE ACTIVE</div>
        </div>`;
      document.body.appendChild(menu);
    }
  }

  /* ══════════════════════════════════════════
     PALETTE
  ══════════════════════════════════════════ */
  function applyPalette(idx) {
    const p = PALETTES[idx % PALETTES.length];
    document.documentElement.style.setProperty('--xc1', p.c1);
    document.documentElement.style.setProperty('--xc2', p.c2);
    const bleed = document.getElementById('x3-color-bleed');
    if (bleed) bleed.style.background =
      `radial-gradient(ellipse at 25% 75%, ${p.c1}55 0%, transparent 55%),
       radial-gradient(ellipse at 75% 25%, ${p.c2}44 0%, transparent 55%)`;
  }

  /* ══════════════════════════════════════════
     BACKGROUND
  ══════════════════════════════════════════ */
  function getBgUrl(idx) {
    return `https://picsum.photos/seed/${(idx % BG_COUNT) + 1}/1920/1080`;
  }

  function loadBg(idx) {
    const img = document.getElementById('x3-bg-img');
    if (!img) return;
    const url = getBgUrl(idx);
    const tmp = new Image();
    tmp.onload = () => {
      img.classList.add('xfade-out');
      setTimeout(() => {
        img.src = url;
        img.classList.remove('xfade-out');
        img.classList.add('xfade-in');
      }, 600);
    };
    tmp.onerror = () => {
      img.src = `https://source.unsplash.com/random/1920x1080?abstract,art&sig=${idx}`;
      img.classList.remove('xfade-out'); img.classList.add('xfade-in');
    };
    tmp.src = url;
  }

  /* ══════════════════════════════════════════
     WATERMARK
  ══════════════════════════════════════════ */
  function cycleWatermark() {
    const wm = document.getElementById('x3-wm');
    if (!wm) return;
    wmFontIdx = Math.floor(Math.random() * WM_FONTS.length);
    wmSizeIdx = Math.floor(Math.random() * WM_SIZES.length);
    wm.style.fontFamily = WM_FONTS[wmFontIdx];
    wm.style.fontSize   = WM_SIZES[wmSizeIdx];
  }

  /* ══════════════════════════════════════════
     FBF
  ══════════════════════════════════════════ */
  function startFBF() {
    const frames = document.querySelectorAll('.x3-fbf-frame');
    if (!frames.length) return;
    setInterval(() => {
      frames[fbfIdx].classList.remove('visible');
      fbfIdx = (fbfIdx + 1) % frames.length;
      frames[fbfIdx].classList.add('visible');
    }, 1000 / FPS);
  }



  /* ══════════════════════════════════════════
     PARALLAX
  ══════════════════════════════════════════ */
  function initParallax() {
    if (window.matchMedia('(pointer: coarse)').matches) return;
    const img = document.getElementById('x3-bg-img');
    if (!img) return;
    document.addEventListener('mousemove', e => {
      requestAnimationFrame(() => {
        const x = (e.clientX / window.innerWidth  - .5) * 14;
        const y = (e.clientY / window.innerHeight - .5) * 14;
        img.style.transform = `translate(${x}px, ${y}px) scale(1.04)`;
      });
    });
  }

  /* ══════════════════════════════════════════
     SCROLL
  ══════════════════════════════════════════ */
  function initScroll() {
    window.addEventListener('scroll', () => {
      const nav = document.getElementById('x3-nav');
      if (nav) nav.classList.toggle('x3-scrolled', window.scrollY > 50);

      const max = Math.max(1, document.body.scrollHeight - window.innerHeight);
      const pct = Math.round(window.scrollY / max * 100);
      const el  = document.getElementById('x3-pct');
      if (el) el.textContent = String(pct).padStart(2, '0');

      /* Update slide dots */
      const dots = document.querySelectorAll('.x3-slide-dot');
      if (dots.length) {
        const di = Math.min(dots.length - 1, Math.floor(pct / (100 / dots.length)));
        dots.forEach((d,i) => d.classList.toggle('x3-active', i === di));
      }
    }, { passive: true });
  }

  /* ══════════════════════════════════════════
     MENU
  ══════════════════════════════════════════ */
  function toggleMenu() {
    closeNotifDropdown();
    menuOpen = !menuOpen;
    document.getElementById('x3-ham')?.classList.toggle('open', menuOpen);
    document.getElementById('x3-menu')?.classList.toggle('open', menuOpen);
    document.body.style.overflow = menuOpen ? 'hidden' : '';
  }
  function closeMenu() { if (menuOpen) toggleMenu(); }

  /* ══════════════════════════════════════════
     NOTIFICATIONS & STATE MANAGEMENT
  ══════════════════════════════════════════ */
  let notifOpen        = false;
  let notifications    = [];
  let lastScansState   = {};
  let lastHistoryIds   = new Set();
  let lastCaptchaState  = new Set();
  let isFirstPoll      = true;

  function loadNotifications() {
    try {
      const stored = localStorage.getItem('x3_notifications');
      if (stored) {
        notifications = JSON.parse(stored);
      } else {
        notifications = [];
      }
    } catch (_) {
      notifications = [];
    }
  }

  function saveNotifications() {
    try {
      localStorage.setItem('x3_notifications', JSON.stringify(notifications));
    } catch (_) {}
  }

  function addNotification(title, desc, type) {
    const notif = {
      id: 'notif_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9),
      title: title,
      desc: desc,
      type: type || 'info', // success, error, info
      unread: true,
      timestamp: Date.now()
    };
    notifications.unshift(notif);
    if (notifications.length > 50) {
      notifications.pop();
    }
    saveNotifications();
    
    if (!isFirstPoll) {
      showToast(title, desc);
      if (Notification.permission === 'granted') {
        try { new Notification(title, { body: desc }); } catch (_) {}
      }
    }
    
    updateBellDot();
    renderNotifications();
  }

  function markAllNotificationsRead() {
    notifications.forEach(n => n.unread = false);
    saveNotifications();
    updateBellDot();
    renderNotifications();
  }

  function updateBellDot() {
    const dot = document.getElementById('x3-bell-dot');
    if (!dot) return;
    const hasUnread = notifications.some(n => n.unread);
    dot.style.display = hasUnread ? 'block' : 'none';
  }

  function formatRelativeTime(ts) {
    const diff = Date.now() - ts;
    if (diff < 5000) return 'Just now';
    const sec = Math.floor(diff / 1000);
    if (sec < 60) return `${sec}s ago`;
    const min = Math.floor(sec / 60);
    if (min < 60) return `${min}m ago`;
    const hr = Math.floor(min / 60);
    if (hr < 24) return `${hr}h ago`;
    return new Date(ts).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  }

  function renderNotifications() {
    const list = document.getElementById('x3-notif-list');
    if (!list) return;
    
    if (notifications.length === 0) {
      list.innerHTML = `<div class="x3-notif-empty">No notifications</div>`;
      return;
    }
    
    list.innerHTML = notifications.map(n => {
      let iconChar = 'ℹ';
      if (n.type === 'success') iconChar = '✓';
      if (n.type === 'error') iconChar = '⚠';
      
      return `
        <div class="x3-notif-item ${n.unread ? 'unread' : ''}" data-id="${n.id}">
          <div class="x3-notif-icon ${n.type}">${iconChar}</div>
          <div class="x3-notif-content">
            <div class="x3-notif-title">${n.title}</div>
            <div class="x3-notif-desc">${n.desc}</div>
            <div class="x3-notif-time">${formatRelativeTime(n.timestamp)}</div>
          </div>
        </div>
      `;
    }).join('');
  }

  function toggleNotifDropdown() {
    closeMenu();
    notifOpen = !notifOpen;
    const dropdown = document.getElementById('x3-notif-dropdown');
    if (dropdown) {
      dropdown.classList.toggle('open', notifOpen);
      if (notifOpen) {
        renderNotifications();
      }
    }
  }

  function closeNotifDropdown() {
    if (notifOpen) {
      notifOpen = false;
      document.getElementById('x3-notif-dropdown')?.classList.remove('open');
    }
  }

  function showToast(title, body) {
    const toast = document.getElementById('x3-toast');
    if (!toast) return;
    document.getElementById('x3-toast-title').textContent = title;
    document.getElementById('x3-toast-body').textContent  = body;
    toast.classList.add('show');
    clearTimeout(toast._t);
    toast._t = setTimeout(() => toast.classList.remove('show'), 4800);
  }
  function closeToast() { document.getElementById('x3-toast')?.classList.remove('show'); }

  async function requestNotif() {
    if (!('Notification' in window)) { showToast('◈ XTREME', 'Notifications not supported.'); return; }
    if (Notification.permission === 'granted') return;
    await Notification.requestPermission();
  }

  /* ══════════════════════════════════════════
     REAL-TIME EVENT POLLER
  ══════════════════════════════════════════ */
  async function pollEvents() {
    try {
      const scanPromise = fetch('/api/scan/status')
        .then(r => r.ok ? r.json() : null)
        .catch(() => null);
      
      const dataPromise = fetch('/api/data')
        .then(r => r.ok ? r.json() : null)
        .catch(() => null);
      
      const histPromise = fetch('/api/history?page=1&per=10')
        .then(r => r.ok ? r.json() : null)
        .catch(() => null);
      
      const [scanRes, dataRes, histRes] = await Promise.all([scanPromise, dataPromise, histPromise]);
      
      if (scanRes && scanRes.scans) {
        const currentScans = scanRes.scans;
        
        for (const [key, val] of Object.entries(currentScans)) {
          const status = val.status;
          const guildName = val.guild_name;
          const prevStatus = lastScansState[key];
          
          if (prevStatus === undefined) {
            if (!isFirstPoll) {
              if (status === 'scanning' || status === 'processing') {
                addNotification('Scan Started', `Scan started for server: ${guildName}`, 'info');
              } else if (status === 'done') {
                addNotification('Scan Completed', `Scan completed for server: ${guildName}`, 'success');
              } else if (status === 'failed') {
                addNotification('Scan Failed', `Scan failed for server: ${guildName}`, 'error');
              }
            }
          } else if (prevStatus !== status) {
            if (status === 'done') {
              addNotification('Scan Completed', `Scan completed for server: ${guildName}`, 'success');
            } else if (status === 'failed') {
              addNotification('Scan Failed', `Scan failed for server: ${guildName}`, 'error');
            } else if (status === 'scanning' || status === 'processing') {
              addNotification('Scan Resumed', `Scan resumed for server: ${guildName}`, 'info');
            }
          }
          
          lastScansState[key] = status;
        }
        
        for (const key of Object.keys(lastScansState)) {
          if (!currentScans[key]) {
            delete lastScansState[key];
          }
        }
      }
      
      if (histRes && histRes.items) {
        const items = histRes.items;
        
        for (let i = items.length - 1; i >= 0; i--) {
          const item = items[i];
          if (!lastHistoryIds.has(item.id)) {
            if (!isFirstPoll) {
              if (item.success) {
                addNotification(
                  'Catch Success!',
                  `Caught ${item.display_name || item.pokemon_name} (IV: ${item.iv}, Lvl: ${item.level})`,
                  'success'
                );
              } else {
                addNotification(
                  'Catch Failed',
                  `Failed to catch ${item.display_name || item.pokemon_name}. Reason: ${item.failure_reason || 'Unknown'}`,
                  'error'
                );
              }
            }
            lastHistoryIds.add(item.id);
          }
        }
      }
      
      if (dataRes && dataRes.captcha) {
        const captchaActive = dataRes.captcha.active || {};
        
        for (const [label, val] of Object.entries(captchaActive)) {
          if (!lastCaptchaState.has(label)) {
            if (!isFirstPoll) {
              addNotification('Captcha Detected!', `Captcha detected on node: ${label}. Action required!`, 'error');
            }
            lastCaptchaState.add(label);
          }
        }
        
        for (const label of Array.from(lastCaptchaState)) {
          if (!captchaActive[label]) {
            if (!isFirstPoll) {
              addNotification('Captcha Resolved', `Captcha resolved on node: ${label}. Resuming operations.`, 'success');
            }
            lastCaptchaState.delete(label);
          }
        }
      }
      
      isFirstPoll = false;
    } catch (e) {
      console.error('Poller error:', e);
    }
  }

  function startPoller() {
    pollEvents().then(() => {
      setInterval(pollEvents, 5000);
    });
  }

  /* ══════════════════════════════════════════
     PAGE LOADER
  ══════════════════════════════════════════ */
  function initLoader() {
    window.addEventListener('load', () => {
      setTimeout(() => {
        document.getElementById('x3-loader')?.classList.add('done');
        setTimeout(() => showToast('◈ XTREME — New Era', 'Every refresh is a new world.'), 400);
      }, 1600);
    });
  }

  /* ══════════════════════════════════════════
     SMOOTH PAGE TRANSITIONS
  ══════════════════════════════════════════ */
  function initTransitions() {
    setTimeout(() => {
      document.querySelectorAll('a:not([data-xtr])').forEach(a => {
        if (a.hostname !== window.location.hostname) return;
        if (a.target === '_blank') return;
        const href = a.getAttribute('href') || '';
        if (!href || href.startsWith('#') || href.startsWith('javascript') || href.startsWith('mailto')) return;
        a.setAttribute('data-xtr', '1');
        a.addEventListener('click', e => {
          e.preventDefault();
          document.body.style.opacity = '0';
          document.body.style.transition = 'opacity .3s ease';
          setTimeout(() => { window.location.href = a.href; }, 320);
        });
      });
    }, 250);
  }

  /* ══════════════════════════════════════════
     CYCLES
  ══════════════════════════════════════════ */
  function startCycles() {
    /* BG + palette cycle */
    setInterval(() => {
      bgIdx++; palIdx++;
      applyPalette(palIdx);
      loadBg(bgIdx);
    }, BG_INTERVAL);

    /* Watermark cycle */
    setInterval(cycleWatermark, WM_INTERVAL);
  }

  /* ══════════════════════════════════════════
     MAIN INIT
  ══════════════════════════════════════════ */
  function init() {
    if (initialized) return;
    initialized = true;

    injectFonts();
    injectCSS();
    buildShell();
    buildNav();

    /* Initial palette & BG */
    applyPalette(palIdx);
    cycleWatermark();
    loadBg(bgIdx);

    /* Engines */
    startFBF();
    initParallax();
    initScroll();
    initLoader();
    initTransitions();
    startCycles();

    /* Load stored notifications */
    loadNotifications();
    updateBellDot();

    /* Start background event poller */
    startPoller();

    /* Close dropdowns on outside click */
    document.addEventListener('click', () => {
      closeNotifDropdown();
    });

    /* ESC closes menu and dropdowns */
    document.addEventListener('keydown', e => {
      if (e.key === 'Escape') {
        closeMenu();
        closeNotifDropdown();
      }
    });

    /* Fade body in */
    requestAnimationFrame(() => {
      requestAnimationFrame(() => {
        document.body.classList.add('x3-visible');
      });
    });
  }

  /* ══════════════════════════════════════════
     PUBLIC API
  ══════════════════════════════════════════ */
  window.XUI = { toggleMenu, closeMenu, requestNotif, showToast, closeToast, toggleNotifDropdown, closeNotifDropdown, markAllNotificationsRead };

  /* Run */
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }

})();
