
        // ── TICKER ──
        (function () {
            const words = ['KAIZER', '×', 'DESIGN', '×', 'MOTION', '×', 'PURPOSE', '×', 'KAIZER', '×', 'DESIGN', '×', 'MOTION', '×', 'PURPOSE', '×'];
            const t = document.getElementById('tickerTrack');
            if (!t) return;
            const frag = words.map(w => { const s = document.createElement('span'); s.className = 'ticker-item'; s.textContent = w; return s });
            const frag2 = frag.map(el => el.cloneNode(true));
            frag.forEach(el => t.appendChild(el));
            frag2.forEach(el => t.appendChild(el));
        })();

        // ── CHARACTER SPLIT HERO ──
        (function () {
            const el = document.getElementById('heroName');
            if (!el) return;
            const text = el.textContent;
            el.textContent = '';
            text.split('').forEach((ch, i) => {
                const s = document.createElement('span');
                s.className = 'char display';
                s.textContent = ch == ' ' ? '\u00a0' : ch;
                s.style.transitionDelay = (i * 38) + 'ms';
                el.appendChild(s);
            });
            // trigger after short delay
            el.querySelectorAll('.char').forEach(c => c.classList.add('in'));
            const sub = document.getElementById('heroSub');
            if (sub) sub.classList.add('in');
            const tag = document.getElementById('heroTag');
            if (tag) tag.classList.add('in');
        })();

        // ── WIPE TRANSITION ──
        const wipe = document.getElementById('wipe');
        const wipeColors = ['#4ECDC4', '#0D0D0D', '#FF3800', '#C9A84C'];
        let lastSection = -1, wiping = false;

        function doWipe(color, cb) {
            if (!wipe || wiping) return;
            wiping = true;
            wipe.style.background = color;
            wipe.style.transition = 'transform 0.22s cubic-bezier(0.77,0,0.175,1)';
            wipe.style.transform = 'translateX(0)';
            setTimeout(() => {
                cb();
                wipe.style.transition = 'transform 0.22s cubic-bezier(0.77,0,0.175,1)';
                wipe.style.transform = 'translateX(100%)';
                setTimeout(() => {
                    wipe.style.transition = 'none';
                    wipe.style.transform = 'translateX(-100%)';
                    wiping = false;
                }, 230);
            }, 230);
        }

        // ── INTERSECTION OBSERVER ──
        const sections = [
            document.getElementById('s01'),
            document.getElementById('s02'),
            document.getElementById('s03'),
            document.getElementById('s04'),
            document.getElementById('s05'),
        ].filter(Boolean);

        // per-section reveal targets
        const revealMaps = {
            's02': [
                { el: 'bigMake', cls: 'in', delay: 0 },
                { el: 'bigAwesome', cls: 'in', delay: 0 },
                { el: 'micro', cls: 'in', delay: 0 },
                { el: 'scrollLabel', cls: 'in', delay: 0 },
            ],
            's03': [
                { el: 'innov', cls: 'in', delay: 0 },
                { el: 'purp', cls: 'in', delay: 0 },
                { el: 'morphShape', cls: 'in', delay: 0 },
                { el: 'dragRing', cls: 'in', delay: 0 },
                { el: 'dragHint', cls: 'in', delay: 0 },
                { el: 'pwrBot', cls: 'in', delay: 0 },
            ],
            's04': [
                { el: 'ml0', cls: 'in', delay: 0 },
                { el: 'ml1', cls: 'in', delay: 0 },
                { el: 'gd', cls: 'in', delay: 0 },
                { el: 'ml2', cls: 'in', delay: 0 },
                { el: 'ml3', cls: 'in', delay: 0 },
                { el: 'mBody', cls: 'in', delay: 0 },
                { el: 'ctaBtn', cls: 'in', delay: 0 },
            ],
            's05': [
                { el: 'cLet', cls: 'in', delay: 0 },
                { el: 'cCreate', cls: 'in', delay: 0 },
                { el: 'emailRow', cls: 'in', delay: 0 },
                { el: 'subArrow', cls: 'in', delay: 0 },
                { el: 'footerTag', cls: 'in', delay: 0 },
            ],
        };

        // zoom elements that scale on scroll
        const zoomEls = document.querySelectorAll('.big-make,.big-awesome,.innovate-text,.purpose-text,.contact-title-let,.contact-title-create');
        zoomEls.forEach(el => { el.style.willChange = 'transform,clip-path,opacity' });

        function triggerSection(id) {
            const map = revealMaps[id];
            if (!map) return;
            map.forEach(({ el, cls, delay }) => {
                const node = document.getElementById(el);
                if (!node) return;
                setTimeout(() => node.classList.add(cls), delay);
            });
        }

        if (sections.length > 0) {
            const obsOpts = { threshold: 0.35 };
            const obs = new IntersectionObserver((entries) => {
                entries.forEach(entry => {
                    if (!entry.isIntersecting) return;
                    const id = entry.target.id;
                    const idx = sections.findIndex(s => s === entry.target);
                    if (idx > 0 && idx !== lastSection) {
                        triggerSection(id);
                    }
                    lastSection = idx;
                });
            }, obsOpts);

            sections.forEach(s => obs.observe(s));
        }

        // ── ZOOM on SCROLL ──
        if (zoomEls.length > 0) {
            const zoomObsOpts = { threshold: [0, 0.2, 0.5, 0.8, 1] };
            const zoomObs = new IntersectionObserver((entries) => {
                entries.forEach(entry => {
                    const r = entry.intersectionRatio;
                    const sc = 1 + (1 - Math.min(r, 1)) * 0.15;
                    entry.target.style.transform = `scale(${sc.toFixed(3)})`;
                });
            }, zoomObsOpts);
            zoomEls.forEach(el => zoomObs.observe(el));
        }

        // ── MORPH DRAG ──
        (function () {
            const shape = document.getElementById('morphShape');
            if (!shape) return;
            let ox = 0, oy = 0, active = false;
            shape.addEventListener('touchstart', e => {
                active = true;
                const t = e.touches[0];
                ox = t.clientX; oy = t.clientY;
                shape.style.cursor = 'grabbing';
                e.preventDefault();
            }, { passive: false });
            window.addEventListener('touchmove', e => {
                if (!active) return;
                const t = e.touches[0];
                const dx = Math.max(-30, Math.min(30, t.clientX - ox));
                const dy = Math.max(-30, Math.min(30, t.clientY - oy));
                shape.style.transform = `translate(calc(-50% + ${dx}px), calc(-50% + ${dy}px)) scale(1)`;
            }, { passive: true });
            window.addEventListener('touchend', () => {
                if (!active) return;
                active = false;
                shape.style.cursor = 'grab';
                shape.style.transition = 'transform 0.6s cubic-bezier(0.34,1.56,0.64,1)';
                shape.style.transform = 'translate(-50%,-50%) scale(1)';
                setTimeout(() => { shape.style.transition = '' }, 700);
            });
        })();

        // ── SUBMIT EMAIL ──
        const subArrowEl = document.getElementById('subArrow');
        if (subArrowEl) {
            subArrowEl.addEventListener('click', () => {
                const inp = document.getElementById('emailInp');
                const val = inp ? inp.value.trim() : '';
                if (val) { alert('KAIZER — Message received.'); }
            });
        }