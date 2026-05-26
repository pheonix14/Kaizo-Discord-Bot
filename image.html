class LuxuryThemeEngine {
    constructor() {
        this.themes = [
            { name: "Space Universe", bg: "https://images.unsplash.com/photo-1462331940025-496dfbfc7564?q=80&w=2000&auto=format&fit=crop" },
            { name: "Nebula Glow", bg: "https://images.unsplash.com/photo-1464802686167-b939a6910659?q=80&w=2000&auto=format&fit=crop" },
            { name: "Cyber Black", bg: "https://images.unsplash.com/photo-1550684848-fac1c5b4e853?q=80&w=2000&auto=format&fit=crop" },
            { name: "Deep Ocean", bg: "https://images.unsplash.com/photo-1518837695005-2083093ee35b?q=80&w=2000&auto=format&fit=crop" },
            { name: "Aurora Sky", bg: "https://images.unsplash.com/photo-1531366936337-7c912a4589a7?q=80&w=2000&auto=format&fit=crop" },
            { name: "Desert Dunes", bg: "https://images.unsplash.com/photo-1509316785289-025f5b846b35?q=80&w=2000&auto=format&fit=crop" },
            { name: "Dark Forest", bg: "https://images.unsplash.com/photo-1511497584788-876760111969?q=80&w=2000&auto=format&fit=crop" },
            { name: "Futuristic City", bg: "https://images.unsplash.com/photo-1515630278258-407f66498911?q=80&w=2000&auto=format&fit=crop" }
        ];

        this.initDOM();
        this.applyRandomTheme();
        this.initParallax();
        this.initParticles();
        this.smoothPageEnter();
    }

    initDOM() {
        if(!document.getElementById('luxury-bg')) {
            const bg = document.createElement('div');
            bg.id = 'luxury-bg';
            bg.style.cssText = `
                position: fixed; top: -5%; left: -5%; width: 110%; height: 110%;
                background-size: cover; background-position: center; z-index: -100;
                transition: transform 0.1s ease-out, opacity 1s ease-in-out;
                filter: brightness(0.7) contrast(1.1);
            `;
            document.body.appendChild(bg);
            
            const overlay = document.createElement('div');
            overlay.style.cssText = `
                position: fixed; inset: 0; background: radial-gradient(circle at center, transparent 0%, #000 120%);
                z-index: -90; pointer-events: none;
            `;
            document.body.appendChild(overlay);

            const canvas = document.createElement('canvas');
            canvas.id = 'luxury-particles';
            canvas.style.cssText = `
                position: fixed; inset: 0; width: 100%; height: 100%;
                z-index: -95; pointer-events: none; opacity: 0.6;
            `;
            document.body.appendChild(canvas);
            
            // Mobile Responsive CSS
            const style = document.createElement('style');
            style.innerHTML = `
                @media (max-width: 768px) {
                    main { flex-direction: column !important; padding: 1rem !important; gap: 1.5rem !important; }
                    .md\\:w-80 { width: 100% !important; }
                    .glass { padding: 1.25rem !important; }
                    .nav-links { 
                        display: none; 
                        flex-direction: column; 
                        position: fixed; 
                        top: 4.5rem; 
                        left: 1rem; 
                        right: 1rem; 
                        background: rgba(10,10,10,0.95); 
                        padding: 1.5rem; 
                        border-radius: 1.5rem;
                        border: 1px solid rgba(255,255,255,0.15); 
                        z-index: 9999999; 
                        backdrop-filter: blur(40px); 
                        gap: 1rem !important; 
                        box-shadow: 0 25px 60px rgba(0,0,0,0.9);
                    }
                    .nav-links.active { display: flex !important; }
                    .hamburger { display: block !important; position: relative; z-index: 10000000; }
                    h1 { font-size: 1.25rem !important; }
                    #console-container { height: 60vh !important; }
                    .history-card { flex-direction: column !important; gap: 1rem !important; }
                    .history-img { width: 100% !important; height: 180px !important; }
                }
                .hamburger { display: none; cursor: pointer; padding: 0.5rem; }
                .hamburger div { width: 25px; height: 2px; background: white; margin: 5px 0; transition: 0.3s; border-radius: 2px; }
            `;
            document.head.appendChild(style);

            // Setup Hamburger Menu
            setTimeout(() => {
                const nav = document.querySelector('nav');
                if (nav) {
                    nav.style.zIndex = '9999999'; // Ensure nav escapes stacking context
                    const linksContainer = nav.querySelector('.flex.gap-4');
                    if (linksContainer) {
                        linksContainer.classList.add('nav-links');
                        const hamburger = document.createElement('div');
                        hamburger.className = 'hamburger';
                        hamburger.innerHTML = '<div></div><div></div><div></div>';
                        hamburger.onclick = () => linksContainer.classList.toggle('active');
                        
                        const title = nav.querySelector('h1');
                        if (title) title.after(hamburger);
                    }
                }
            }, 100);
        }
    }

    applyRandomTheme() {
        const theme = this.themes[Math.floor(Math.random() * this.themes.length)];
        const bg = document.getElementById('luxury-bg');
        bg.style.opacity = '0';
        
        const img = new Image();
        img.src = theme.bg;
        img.onload = () => {
            bg.style.backgroundImage = `url('${theme.bg}')`;
            bg.style.opacity = '1';
        };
    }

    initParallax() {
        document.addEventListener('mousemove', (e) => {
            requestAnimationFrame(() => {
                const x = (e.clientX / window.innerWidth - 0.5) * 20;
                const y = (e.clientY / window.innerHeight - 0.5) * 20;
                const bg = document.getElementById('luxury-bg');
                if (bg) bg.style.transform = `translate(${x}px, ${y}px) scale(1.05)`;
            });
        });
    }

    initParticles() {
        const canvas = document.getElementById('luxury-particles');
        const ctx = canvas.getContext('2d');
        canvas.width = window.innerWidth;
        canvas.height = window.innerHeight;

        const particles = Array.from({length: 60}).map(() => ({
            x: Math.random() * canvas.width,
            y: Math.random() * canvas.height,
            size: Math.random() * 2,
            speedY: Math.random() * 0.5 + 0.1,
            opacity: Math.random() * 0.5 + 0.1
        }));

        const render = () => {
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            particles.forEach(p => {
                ctx.fillStyle = `rgba(255, 255, 255, ${p.opacity})`;
                ctx.beginPath();
                ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2);
                ctx.fill();
                p.y -= p.speedY;
                if (p.y < 0) p.y = canvas.height;
            });
            requestAnimationFrame(render);
        };
        render();

        window.addEventListener('resize', () => {
            canvas.width = window.innerWidth;
            canvas.height = window.innerHeight;
        });
    }

    smoothPageEnter() {
        document.body.style.opacity = '0';
        document.body.style.transition = 'opacity 0.8s cubic-bezier(0.16, 1, 0.3, 1)';
        requestAnimationFrame(() => {
            document.body.style.opacity = '1';
        });

        // Intercept links for smooth exit
        document.querySelectorAll('a').forEach(a => {
            if (a.hostname === window.location.hostname && a.target !== '_blank') {
                a.addEventListener('click', (e) => {
                    e.preventDefault();
                    document.body.style.opacity = '0';
                    setTimeout(() => window.location.href = a.href, 500);
                });
            }
        });
    }
}

document.addEventListener('DOMContentLoaded', () => {
    window.ThemeEngine = new LuxuryThemeEngine();
});
