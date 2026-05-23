function initializeDashboardScripts() {
    // ALWAYS fade out loader first to prevent infinite loading screens
    initVisualEffects();
    
    // Determine current page route
    const path = window.location.pathname;
    
    try {
        if (path.includes("/dashboard")) {
            initDashboard();
        } else if (path.includes("/logs")) {
            initLogsPage();
        }
    } catch(e) { console.error("Error in page init:", e); }

    // Initialize real-time status and health reloader
    try {
        updateBotConnectionStatus();
        startServerStatusWatcher();
    } catch(e) { console.error("Error in status watcher:", e); }
}

if (document.readyState === 'loading') {
    document.addEventListener("DOMContentLoaded", initializeDashboardScripts);
} else {
    initializeDashboardScripts();
}

// --- TOAST NOTIFICATIONS ---
function showToast(message, type = "success") {
    const toast = document.getElementById("notif-toast");
    const titleEl = document.getElementById("nt-title");
    const bodyEl = document.getElementById("nt-body");
    
    if (toast && titleEl && bodyEl) {
        titleEl.textContent = type === "success" ? "◈ KAIZER K5 — SUCCESS" : "⚠️ KAIZER K5 — ERROR";
        bodyEl.textContent = message;
        toast.style.borderLeftColor = type === "success" ? "var(--c2)" : "var(--c1)";
        toast.classList.add("show");
        
        setTimeout(() => {
            toast.classList.remove("show");
        }, 4500);
    } else {
        // Fallback if not using navigationbar
        let fb = document.getElementById("toast-notification");
        if (!fb) {
            fb = document.createElement("div");
            fb.id = "toast-notification";
            fb.className = "alert-toast glass-panel";
            document.body.appendChild(fb);
        }
        fb.className = `alert-toast glass-panel ${type} show`;
        fb.innerHTML = `
            <span class="toast-icon">${type === 'success' ? '✅' : '❌'}</span>
            <span class="toast-message">${message}</span>
        `;
        setTimeout(() => {
            fb.classList.remove("show");
        }, 3500);
    }
}

function closeToast() {
    const toast = document.getElementById("notif-toast");
    if (toast) {
        toast.classList.remove("show");
    }
}

// --- BROWSER NOTIFICATIONS ---
async function requestNotif() {
    const NOTIF_MSGS = [
      {t: '◈ Kaizer K5 Security', b: 'Server protections are active and monitoring logs.'},
      {t: '⬡ Anti-Nuke Active', b: 'Configured thresholds are guarded in real-time.'},
      {t: '◉ Audit Log Node', b: 'Live sync with Supabase is running with RLS.'},
      {t: '◎ Node Health', b: 'Web latency and Discord connection are healthy.'}
    ];
    
    if (!('Notification' in window)) {
        showToast('Notifications not supported in this browser.', 'error');
        return;
    }
    
    const sendNotif = () => {
        const msg = NOTIF_MSGS[Math.floor(Math.random() * NOTIF_MSGS.length)];
        try {
            new Notification(msg.t, { body: msg.b });
        } catch (e) {
            showToast(msg.b, 'success');
        }
        showToast(msg.b, 'success');
    }
    
    if (Notification.permission === 'granted') {
        sendNotif();
    } else if (Notification.permission !== 'denied') {
        const perm = await Notification.requestPermission();
        if (perm === 'granted') {
            sendNotif();
        }
    } else {
        showToast('Please enable notifications in your browser settings.', 'error');
    }
}

// --- HAMBURGER & OVERLAY NAVIGATION ---
let menuOpen = false;
function toggleMenu() {
    menuOpen = !menuOpen;
    const ham = document.getElementById('ham');
    const overlay = document.getElementById('menu-overlay');
    if (ham) ham.classList.toggle('open', menuOpen);
    if (overlay) overlay.classList.toggle('open', menuOpen);
    document.body.style.overflow = menuOpen ? 'hidden' : '';
}
function closeMenu() {
    if (menuOpen) toggleMenu();
}

// --- VISUAL EFFECTS SYSTEM ---
function initVisualEffects() {
    // 1. Page Loader Fade Out
    const loader = document.getElementById('loader');
    if (loader) {
        setTimeout(() => {
            loader.classList.add('done');
        }, 1000);
    }

    // 2. Custom Cursor Rings
    const cur = document.getElementById('cursor');
    const ring = document.getElementById('cursor-ring');
    let mx = 0, my = 0, rx = 0, ry = 0;
    
    if (cur && ring) {
        document.addEventListener('mousemove', e => {
            mx = e.clientX;
            my = e.clientY;
            cur.style.left = mx - 6 + 'px';
            cur.style.top = my - 6 + 'px';
        });
        
        function animRing() {
            rx += (mx - rx) * 0.12;
            ry += (my - ry) * 0.12;
            ring.style.left = rx - 18 + 'px';
            ring.style.top = ry - 18 + 'px';
            requestAnimationFrame(animRing);
        }
        animRing();
        
        // Cursor scale-up on interactive elements
        function setupCursorHover() {
            document.querySelectorAll('a, button, .card, .stat-box, .glass-panel, input, label, .slider, select, option').forEach(el => {
                if (el.dataset.cursorBound) return;
                el.dataset.cursorBound = "true";
                el.addEventListener('mouseenter', () => {
                    cur.style.transform = 'scale(3)';
                    ring.style.borderColor = 'var(--c1)';
                });
                el.addEventListener('mouseleave', () => {
                    cur.style.transform = 'scale(1)';
                    ring.style.borderColor = 'rgba(255,255,255,0.5)';
                });
            });
        }
        setupCursorHover();
        setInterval(setupCursorHover, 1000);
    }

    // 3. Rotating Watermark Font / Size
    const wm = document.getElementById('wm');
    const WM_FONTS = [
      "'Bebas Neue',sans-serif",
      "'Orbitron',sans-serif",
      "'Abril Fatface',serif",
      "'Righteous',sans-serif",
      "'Cinzel Decorative',serif",
      "'Monoton',cursive",
      "'Black Han Sans',sans-serif",
      "'Dancing Script',cursive",
      "'Playfair Display',serif",
      "'Permanent Marker',cursive"
    ];
    const WM_SIZES = ['10vw', '12vw', '14vw', '16vw', '18vw'];
    
    function setWatermark() {
        if (!wm) return;
        const fi = Math.floor(Math.random() * WM_FONTS.length);
        const si = Math.floor(Math.random() * WM_SIZES.length);
        wm.style.fontFamily = WM_FONTS[fi];
        wm.style.fontSize = WM_SIZES[si];
    }
    if (wm) {
        setWatermark();
        setInterval(setWatermark, 8000);
    }

    // 4. Color Bleed Dynamic Gradient Rotation
    const colorBleed = document.getElementById('colorBleed');
    const COLORS = [
      ['#ff2d55', '#0affe4'],
      ['#ff6b35', '#c7ff3a'],
      ['#a855f7', '#22d3ee'],
      ['#f59e0b', '#f43f5e'],
      ['#10b981', '#6366f1'],
      ['#ec4899', '#fbbf24']
    ];
    let colorIdx = Math.floor(Math.random() * COLORS.length);
    
    function applyColors(i) {
        if (!colorBleed) return;
        const [c1, c2] = COLORS[i % COLORS.length];
        document.documentElement.style.setProperty('--c1', c1);
        document.documentElement.style.setProperty('--c2', c2);
        colorBleed.style.background = `radial-gradient(ellipse at 30% 70%, ${c1}44, transparent 60%), radial-gradient(ellipse at 70% 30%, ${c2}33, transparent 60%)`;
    }
    if (colorBleed) {
        applyColors(colorIdx);
        setInterval(() => {
            colorIdx++;
            applyColors(colorIdx);
        }, 12000);
    }

    // 5. Navbar Scrolled Background Blurs
    window.addEventListener('scroll', () => {
        const navbar = document.getElementById('navbar');
        if (navbar) {
            navbar.classList.toggle('scrolled', window.scrollY > 60);
        }
    });

    // 6. Populate Marquee Track (if on home page)
    const mq = document.getElementById('mq');
    if (mq) {
        const MQ_ITEMS = ['Kaizer K5 Protection', 'Anti-Nuke Engine', 'Supabase Backed & RLS Enabled', 'Anti-Mass Ban / Kick', '◈', 'Anti-Channel Deletion', 'Live Events Monitoring', 'Admin Whitelisting', '⬡', 'Ultimate Discord Defense'];
        const fill = [...MQ_ITEMS, ...MQ_ITEMS, ...MQ_ITEMS, ...MQ_ITEMS];
        fill.forEach(txt => {
            const d = document.createElement('div');
            d.className = 'marquee-item';
            d.innerHTML = `<span class="dot"></span>${txt}`;
            mq.appendChild(d);
        });
    }
}

// --- DYNAMIC STATUS & HEALTH POLLER ---
function updateBotConnectionStatus() {
    const dot = document.getElementById("bot-status-dot");
    const text = document.getElementById("bot-status-text");
    const authDot = document.getElementById("auth-status-dot");
    const authText = document.getElementById("auth-status-text");
    
    async function check() {
        try {
            const res = await fetch("/api/status");
            if (res.ok) {
                const data = await res.json();
                if (data.status === "online") {
                    if (dot) dot.className = "status-dot online";
                    if (text) text.textContent = "Online";
                    if (authDot) authDot.className = "status-dot online";
                    if (authText) authText.textContent = "Node Online & Monitoring";
                    return;
                }
            }
            if (dot) dot.className = "status-dot";
            if (text) text.textContent = "Offline";
            if (authDot) authDot.className = "status-dot";
            if (authText) authText.textContent = "Node Offline / Reconnecting";
        } catch (err) {
            if (dot) dot.className = "status-dot";
            if (text) text.textContent = "Offline";
            if (authDot) authDot.className = "status-dot";
            if (authText) authText.textContent = "Node Offline / Reconnecting";
        }
    }
    
    check();
    setInterval(check, 5000);
}

function startServerStatusWatcher() {
    let isOffline = false;
    setInterval(async () => {
        try {
            const res = await fetch("/health");
            if (res.ok) {
                if (isOffline) {
                    isOffline = false;
                    showToast("Connection re-established. Reloading active tab...", "success");
                    setTimeout(() => {
                        window.location.reload();
                    }, 1000);
                }
            } else {
                isOffline = true;
            }
        } catch (err) {
            isOffline = true;
        }
    }, 2000);
}

// --- DASHBOARD API & CONTROL LOGIC ---
function initDashboard() {
    const settingsForm = document.getElementById("settings-form");
    const whitelistForm = document.getElementById("whitelist-form");
    const whitelistInput = document.getElementById("whitelist-userid");
    const whitelistList = document.getElementById("whitelist-container");
    
    // 1. Sidebar Tab Switching
    const tabBtns = document.querySelectorAll(".dashboard-tab-btn");
    const tabContents = document.querySelectorAll(".tab-content");
    
    tabBtns.forEach(btn => {
        btn.addEventListener("click", () => {
            const targetTab = btn.dataset.tab;
            
            // Remove active classes
            tabBtns.forEach(b => b.classList.remove("active"));
            tabContents.forEach(c => c.classList.remove("active"));
            
            // Add active class
            btn.classList.add("active");
            const targetContent = document.getElementById(`tab-${targetTab}`);
            if (targetContent) {
                targetContent.classList.add("active");
            }
            
            // Save to localStorage
            localStorage.setItem("dashboard_active_tab", targetTab);
        });
    });
    
    // Restore active tab
    const savedTab = localStorage.getItem("dashboard_active_tab");
    if (savedTab) {
        const matchingBtn = document.querySelector(`.dashboard-tab-btn[data-tab="${savedTab}"]`);
        if (matchingBtn) {
            matchingBtn.click();
        }
    }

    // 2. Security (Anti-Nuke) Settings Form Submission
    if (settingsForm) {
        settingsForm.addEventListener("submit", async (e) => {
            e.preventDefault();
            
            const submitBtn = settingsForm.querySelector("button[type='submit']");
            const originalText = submitBtn.innerHTML;
            submitBtn.innerHTML = "<span>Saving Parameters...</span>";
            submitBtn.disabled = true;
            
            // Gather values
            const payload = {
                anti_ban_limit: parseInt(document.getElementById("anti_ban_limit").value),
                anti_ban_time_frame: parseInt(document.getElementById("anti_ban_time_frame").value),
                anti_kick_limit: parseInt(document.getElementById("anti_kick_limit").value),
                anti_kick_time_frame: parseInt(document.getElementById("anti_kick_time_frame").value),
                anti_channel_delete_limit: parseInt(document.getElementById("anti_channel_delete_limit").value),
                anti_channel_delete_time_frame: parseInt(document.getElementById("anti_channel_delete_time_frame").value),
                anti_role_delete_limit: parseInt(document.getElementById("anti_role_delete_limit").value),
                anti_role_delete_time_frame: parseInt(document.getElementById("anti_role_delete_time_frame").value),
                anti_bot_add: document.getElementById("anti_bot_add").checked,
                is_active: document.getElementById("is_active").checked
            };
            
            try {
                const response = await fetch("/api/guild/settings", {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json"
                    },
                    body: JSON.stringify(payload)
                });
                
                const result = await response.json();
                if (response.ok && result.success) {
                    showToast("Security settings saved successfully!", "success");
                } else {
                    showToast(result.error || "Failed to update configurations", "error");
                }
            } catch (err) {
                console.error(err);
                showToast("Connection error. Could not reach the server.", "error");
            } finally {
                submitBtn.innerHTML = originalText;
                submitBtn.disabled = false;
            }
        });
    }
    
    // 3. Whitelist Add User
    if (whitelistForm) {
        whitelistForm.addEventListener("submit", async (e) => {
            e.preventDefault();
            const userId = whitelistInput.value.trim();
            if (!userId) return;
            
            const submitBtn = whitelistForm.querySelector("button");
            const originalText = submitBtn.innerHTML;
            submitBtn.innerHTML = "<span>Adding...</span>";
            submitBtn.disabled = true;
            
            try {
                const response = await fetch("/api/guild/whitelist", {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json"
                    },
                    body: JSON.stringify({ user_id: userId })
                });
                
                const result = await response.json();
                if (response.ok && result.success) {
                    showToast("User added to whitelist!", "success");
                    whitelistInput.value = "";
                    
                    // Appends user item dynamically to DOM list
                    const div = document.createElement("div");
                    div.className = "whitelist-item";
                    div.id = `whitelist-user-${result.user.id}`;
                    div.innerHTML = `
                        <div class="whitelist-user">
                            <div class="whitelist-user-avatar"></div>
                            <div class="whitelist-user-info">
                                <span class="whitelist-username">${result.user.name}</span>
                                <span class="whitelist-userid">${result.user.id}</span>
                            </div>
                        </div>
                        <button class="btn-remove" onclick="removeWhitelistedUser('${result.user.id}')">Remove</button>
                    `;
                    whitelistList.appendChild(div);
                } else {
                    showToast(result.error || "Failed to whitelist user", "error");
                }
            } catch (err) {
                showToast("Connection error while adding to whitelist", "error");
            } finally {
                submitBtn.innerHTML = originalText;
                submitBtn.disabled = false;
            }
        });
    }

    // Generic saveSettings function for the new dashboard tabs
    window.saveSettings = async function(event, category) {
        event.preventDefault();
        const form = event.target;
        const submitBtn = form.querySelector("button[type='submit']");
        const originalText = submitBtn.innerHTML;
        submitBtn.innerHTML = "<span>Saving...</span>";
        submitBtn.disabled = true;

        // Collect all inputs within the form
        const payload = { category: category };
        const inputs = form.querySelectorAll('input, select, textarea');
        inputs.forEach(input => {
            if (!input.id) return;
            if (input.type === 'checkbox') {
                payload[input.id] = input.checked;
            } else if (input.type === 'number') {
                payload[input.id] = parseFloat(input.value) || 0;
            } else {
                payload[input.id] = input.value;
            }
        });

        if (category === 'welcome') {
            // Build Unified Welcome Config Object
            const welcomeConfig = {
                message_type: payload['welcome_embed_enabled'] ? 'embed' : 'text',
                text: payload['welcome_message'] || '',
                embed: {
                    title: payload['welcome_embed_title'] || '',
                    description: payload['welcome_embed_desc'] || '',
                    color: payload['welcome_embed_color_hex'] || '#0affe4',
                    thumbnail: payload['welcome_embed_thumbnail'] || '',
                    image: payload['welcome_embed_image'] || '',
                    footer: payload['welcome_embed_footer'] || '',
                    footer_icon: payload['welcome_embed_footer_icon'] || ''
                },
                image_enabled: !!payload['welcome_image_enabled'],
                image_style: payload['welcome_image_style'] || 'plain_gradient',
                image_color: payload['welcome_image_color'] || 'cyan_neon',
                custom_bg_url: payload['welcome_custom_bg_url'] || '',
                image_elements: {
                    avatar: !!payload['welcome_image_show_avatar'],
                    username: !!payload['welcome_image_show_username'],
                    server_name: !!payload['welcome_image_show_server'],
                    member_count: !!payload['welcome_image_show_count'],
                    custom_text: payload['welcome_image_custom_text'] || ''
                },
                dm_enabled: !!payload['welcome_dm_enabled'],
                dm_type: payload['welcome_dm_embed_enabled'] ? 'embed' : 'text',
                dm_text: payload['welcome_dm_text'] || '',
                dm_embed: {
                    title: payload['welcome_dm_embed_title'] || '',
                    description: payload['welcome_dm_embed_desc'] || '',
                    color: payload['welcome_dm_embed_color_hex'] || '#0affe4',
                    thumbnail: payload['welcome_dm_embed_thumbnail'] || '',
                    image: payload['welcome_dm_embed_image'] || '',
                    footer: payload['welcome_dm_embed_footer'] || '',
                    footer_icon: payload['welcome_dm_embed_footer_icon'] || ''
                }
            };
            payload['welcome_message'] = JSON.stringify(welcomeConfig);

            // Build Unified Goodbye Config Object
            const goodbyeConfig = {
                message_type: payload['goodbye_embed_enabled'] ? 'embed' : 'text',
                text: payload['goodbye_message'] || '',
                embed: {
                    title: payload['goodbye_embed_title'] || '',
                    description: payload['goodbye_embed_desc'] || '',
                    color: payload['goodbye_embed_color_hex'] || '#ef4444',
                    thumbnail: payload['goodbye_embed_thumbnail'] || '',
                    image: payload['goodbye_embed_image'] || '',
                    footer: payload['goodbye_embed_footer'] || '',
                    footer_icon: payload['goodbye_embed_footer_icon'] || ''
                },
                image_enabled: !!payload['goodbye_image_enabled'],
                image_style: payload['goodbye_image_style'] || 'plain_gradient',
                image_color: payload['goodbye_image_color'] || 'cyan_neon',
                custom_bg_url: payload['goodbye_custom_bg_url'] || '',
                image_elements: {
                    avatar: !!payload['goodbye_image_show_avatar'],
                    username: !!payload['goodbye_image_show_username'],
                    server_name: !!payload['goodbye_image_show_server'],
                    member_count: !!payload['goodbye_image_show_count'],
                    custom_text: payload['goodbye_image_custom_text'] || ''
                },
                dm_enabled: !!payload['goodbye_dm_enabled'],
                dm_type: payload['goodbye_dm_embed_enabled'] ? 'embed' : 'text',
                dm_text: payload['goodbye_dm_text'] || '',
                dm_embed: {
                    title: payload['goodbye_dm_embed_title'] || '',
                    description: payload['goodbye_dm_embed_desc'] || '',
                    color: payload['goodbye_dm_embed_color_hex'] || '#ef4444',
                    thumbnail: payload['goodbye_dm_embed_thumbnail'] || '',
                    image: payload['goodbye_dm_embed_image'] || '',
                    footer: payload['goodbye_dm_embed_footer'] || '',
                    footer_icon: payload['goodbye_dm_embed_footer_icon'] || ''
                }
            };
            payload['goodbye_message'] = JSON.stringify(goodbyeConfig);

            // Clean up all frontend helper keys from the payload to avoid database errors
            const keysToRemove = [
                'welcome_embed_enabled', 'welcome_embed_title', 'welcome_embed_color', 'welcome_embed_color_hex',
                'welcome_embed_desc', 'welcome_embed_thumbnail', 'welcome_embed_image', 'welcome_embed_footer', 'welcome_embed_footer_icon',
                'welcome_image_enabled', 'welcome_image_style', 'welcome_image_color', 'welcome_custom_bg_url',
                'welcome_image_show_avatar', 'welcome_image_show_username', 'welcome_image_show_server', 'welcome_image_show_count', 'welcome_image_custom_text',
                'welcome_dm_enabled', 'welcome_dm_embed_enabled', 'welcome_dm_text', 'welcome_dm_embed_title', 'welcome_dm_embed_color', 'welcome_dm_embed_color_hex',
                'welcome_dm_embed_desc', 'welcome_dm_embed_thumbnail', 'welcome_dm_embed_image', 'welcome_dm_embed_footer', 'welcome_dm_embed_footer_icon',
                
                'goodbye_embed_enabled', 'goodbye_embed_title', 'goodbye_embed_color', 'goodbye_embed_color_hex',
                'goodbye_embed_desc', 'goodbye_embed_thumbnail', 'goodbye_embed_image', 'goodbye_embed_footer', 'goodbye_embed_footer_icon',
                'goodbye_image_enabled', 'goodbye_image_style', 'goodbye_image_color', 'goodbye_custom_bg_url',
                'goodbye_image_show_avatar', 'goodbye_image_show_username', 'goodbye_image_show_server', 'goodbye_image_show_count', 'goodbye_image_custom_text',
                'goodbye_dm_enabled', 'goodbye_dm_embed_enabled', 'goodbye_dm_text', 'goodbye_dm_embed_title', 'goodbye_dm_embed_color', 'goodbye_dm_embed_color_hex',
                'goodbye_dm_embed_desc', 'goodbye_dm_embed_thumbnail', 'goodbye_dm_embed_image', 'goodbye_dm_embed_footer', 'goodbye_dm_embed_footer_icon'
            ];
            keysToRemove.forEach(k => delete payload[k]);
        }

        // Use the global guildId variable defined in server.html
        if (typeof guildId === 'undefined') {
            showToast("Guild ID not found.", "error");
            submitBtn.innerHTML = originalText;
            submitBtn.disabled = false;
            return;
        }

        let endpoint = `/api/guild/${guildId}/settings`;
        
        // Route specific categories to their respective endpoints
        if (category === 'reaction_roles') {
            endpoint = `/api/guild/${guildId}/reaction_roles`;
        } else if (category === 'custom_commands') {
            endpoint = `/api/guild/${guildId}/custom_commands`;
        } else if (category === 'giveaways') {
            endpoint = `/api/guild/${guildId}/giveaways`;
        }

        try {
            const response = await fetch(endpoint, {
                method: "PATCH",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload)
            });
            const result = await response.json();
            if (response.ok && result.success) {
                showToast(result.message || "Settings saved successfully!", "success");
            } else {
                showToast(result.error || "Failed to save settings", "error");
            }
        } catch (err) {
            console.error(err);
            showToast("Connection error.", "error");
        } finally {
            submitBtn.innerHTML = originalText;
            submitBtn.disabled = false;
        }
    };


    // 4. Counters Settings Form Submission
    const countersForm = document.getElementById("counters-form");
    if (countersForm) {
        countersForm.addEventListener("submit", async (e) => {
            e.preventDefault();
            
            const submitBtn = countersForm.querySelector("button[type='submit']");
            const originalText = submitBtn.innerHTML;
            submitBtn.innerHTML = "<span>Saving Parameters...</span>";
            submitBtn.disabled = true;
            
            const payload = {
                style: document.getElementById("counter_style").value,
                refresh_interval: document.getElementById("counter_refresh").value,
                category_id: document.getElementById("counter_category").value,
                tracked_vc_id: document.getElementById("counter_tracked_vc").value,
                total_channel_id: document.getElementById("counter_total_chan").value,
                total_format: document.getElementById("counter_total_fmt").value,
                online_channel_id: document.getElementById("counter_online_chan").value,
                online_format: document.getElementById("counter_online_fmt").value,
                offline_channel_id: document.getElementById("counter_offline_chan").value,
                offline_format: document.getElementById("counter_offline_fmt").value,
                invc_channel_id: document.getElementById("counter_invc_chan").value,
                invc_format: document.getElementById("counter_invc_fmt").value
            };
            
            try {
                const response = await fetch("/api/guild/counters", {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json"
                    },
                    body: JSON.stringify(payload)
                });
                
                const result = await response.json();
                if (response.ok && result.success) {
                    showToast("Counters settings saved successfully!", "success");
                } else {
                    showToast(result.error || "Failed to save counters settings", "error");
                }
            } catch (err) {
                showToast("Connection error while saving counters configuration", "error");
            } finally {
                submitBtn.innerHTML = originalText;
                submitBtn.disabled = false;
            }
        });
    }

    // 5. Counters Auto-Generation Trigger
    const btnAutoGenerate = document.getElementById("btn-auto-generate-counters");
    if (btnAutoGenerate) {
        btnAutoGenerate.addEventListener("click", async () => {
            if (!confirm("Are you sure you want to auto-create counter channels inside Discord? This will create a category and 4 voice channels.")) return;
            
            const originalText = btnAutoGenerate.innerHTML;
            btnAutoGenerate.innerHTML = "<span>Generating Channels...</span>";
            btnAutoGenerate.disabled = true;
            
            const payload = {
                style: document.getElementById("counter_style").value,
                refresh_interval: document.getElementById("counter_refresh").value,
                total_format: document.getElementById("counter_total_fmt").value,
                online_format: document.getElementById("counter_online_fmt").value,
                offline_format: document.getElementById("counter_offline_fmt").value,
                invc_format: document.getElementById("counter_invc_fmt").value,
                tracked_vc_id: document.getElementById("counter_tracked_vc").value
            };
            
            try {
                const response = await fetch("/api/guild/counters/auto-generate", {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json"
                    },
                    body: JSON.stringify(payload)
                });
                const result = await response.json();
                if (response.ok && result.success) {
                    showToast("Stats Channels generated successfully! Reloading...", "success");
                    setTimeout(() => {
                        window.location.reload();
                    }, 1500);
                } else {
                    showToast(result.error || "Failed to auto-generate stats channels", "error");
                }
            } catch (err) {
                showToast("Connection error while auto-generating counters.", "error");
            } finally {
                btnAutoGenerate.innerHTML = originalText;
                btnAutoGenerate.disabled = false;
            }
        });
    }

    // 6. Temp VC settings Form Submission
    const tempVcForm = document.getElementById("temp-vc-form");
    if (tempVcForm) {
        tempVcForm.addEventListener("submit", async (e) => {
            e.preventDefault();
            
            const submitBtn = tempVcForm.querySelector("button[type='submit']");
            const originalText = submitBtn.innerHTML;
            submitBtn.innerHTML = "<span>Saving Parameters...</span>";
            submitBtn.disabled = true;
            
            const payload = {
                lobby_channel_id: document.getElementById("temp_vc_lobby").value,
                category_id: document.getElementById("temp_vc_category").value,
                default_name_format: document.getElementById("temp_vc_name_format").value,
                default_limit: parseInt(document.getElementById("temp_vc_limit").value),
                default_locked: document.getElementById("temp_vc_locked").checked
            };
            
            try {
                const response = await fetch("/api/guild/temp-vc", {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json"
                    },
                    body: JSON.stringify(payload)
                });
                
                const result = await response.json();
                if (response.ok && result.success) {
                    showToast("Temp VC settings saved successfully!", "success");
                } else {
                    showToast(result.error || "Failed to save Temp VC settings", "error");
                }
            } catch (err) {
                showToast("Connection error while saving Temp VC config.", "error");
            } finally {
                submitBtn.innerHTML = originalText;
                submitBtn.disabled = false;
            }
        });
    }

    // 7. Decoration Themes Apply Trigger
    const applyButtons = document.querySelectorAll(".btn-apply-decor");
    applyButtons.forEach(btn => {
        btn.addEventListener("click", async () => {
            const themeKey = btn.dataset.theme;
            if (!confirm(`Are you sure you want to apply the "${themeKey}" decoration style to all channels? This will rename channels to match the style pattern.`)) return;
            
            const originalText = btn.innerHTML;
            btn.innerHTML = "<span>Applying...</span>";
            btn.disabled = true;
            
            try {
                const response = await fetch("/api/guild/decor/apply", {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json"
                    },
                    body: JSON.stringify({ theme_key: themeKey })
                });
                const result = await response.json();
                if (response.ok && result.success) {
                    showToast(`Decoration applied! Renamed ${result.success_count} channels successfully.`, "success");
                    setTimeout(() => window.location.reload(), 1500);
                } else {
                    showToast(result.error || "Failed to apply theme", "error");
                }
            } catch (err) {
                showToast("Connection error while applying decoration.", "error");
            } finally {
                btn.innerHTML = originalText;
                btn.disabled = false;
            }
        });
    });

    // 8. Decoration Undo Trigger
    const btnUndoDecor = document.getElementById("btn-undo-decor");
    if (btnUndoDecor) {
        btnUndoDecor.addEventListener("click", async () => {
            if (!confirm("Are you sure you want to restore all channels back to their previous names?")) return;
            
            const originalText = btnUndoDecor.innerHTML;
            btnUndoDecor.innerHTML = "<span>Restoring...</span>";
            btnUndoDecor.disabled = true;
            
            try {
                const response = await fetch("/api/guild/decor/undo", {
                    method: "POST"
                });
                const result = await response.json();
                if (response.ok && result.success) {
                    showToast(`Restored ${result.restored_count} channels back to their original names.`, "success");
                    setTimeout(() => window.location.reload(), 1500);
                } else {
                    showToast(result.error || "Failed to restore decoration backup", "error");
                }
            } catch (err) {
                showToast("Connection error while undoing decoration.", "error");
            } finally {
                btnUndoDecor.innerHTML = originalText;
                btnUndoDecor.disabled = false;
            }
        });
    }

    // 9. Server Template Build Trigger
    const buildButtons = document.querySelectorAll(".btn-build-template");
    buildButtons.forEach(btn => {
        btn.addEventListener("click", async () => {
            const template = btn.dataset.template;
            const card = btn.closest(".template-card");
            const wipeCheckbox = card.querySelector(".wipe-checkbox");
            const wipe = wipeCheckbox ? wipeCheckbox.checked : false;
            
            let msg = `Are you sure you want to build the ${template} channel layout template?`;
            if (wipe) {
                msg = `⚠️ DANGER WARNING ⚠️\n\nYou checked "Wipe Server first". THIS WILL PERMANENTLY DELETE ALL CHANNELS in this Discord server before creating the template. There is NO undo.\n\nAre you absolutely sure you want to proceed?`;
            }
            
            if (!confirm(msg)) return;
            
            const originalText = btn.innerHTML;
            btn.innerHTML = "<span>Building Layout...</span>";
            btn.disabled = true;
            
            try {
                const response = await fetch("/api/guild/build/server", {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json"
                    },
                    body: JSON.stringify({ template: template, wipe: wipe })
                });
                const result = await response.json();
                if (response.ok && result.success) {
                    showToast(`Template built! Created ${result.created_count} channels successfully.`, "success");
                    setTimeout(() => window.location.reload(), 1500);
                } else {
                    showToast(result.error || "Failed to build template", "error");
                }
            } catch (err) {
                showToast("Connection error while building template.", "error");
            } finally {
                btn.innerHTML = originalText;
                btn.disabled = false;
            }
        });
    });
}

// Whitelist Remove User (globally scoped)
async function removeWhitelistedUser(userId) {
    if (!confirm("Are you sure you want to remove this user from the whitelist?")) return;
    
    try {
        const response = await fetch(`/api/guild/whitelist/${userId}`, {
            method: "DELETE"
        });
        
        const result = await response.json();
        if (response.ok && result.success) {
            showToast("User removed from whitelist.", "success");
            const element = document.getElementById(`whitelist-user-${userId}`);
            if (element) {
                element.remove();
            }
        } else {
            showToast(result.error || "Failed to remove user", "error");
        }
    } catch (err) {
        showToast("Error connecting to server.", "error");
    }
}

// --- LOGS PAGE API LOGIC ---
function initLogsPage() {
    const logsBody = document.getElementById("logs-table-body");
    if (!logsBody) return;
    
    async function loadLogs() {
        try {
            const response = await fetch("/api/guild/logs");
            const data = await response.json();
            
            if (!response.ok) {
                logsBody.innerHTML = `<tr><td colspan="5" style="text-align: center; color: var(--c1);">Failed to load security logs.</td></tr>`;
                return;
            }
            
            if (!data.logs || data.logs.length === 0) {
                logsBody.innerHTML = `<tr><td colspan="5" style="text-align: center; color: var(--text-muted);">No security logs found. Your server is secure.</td></tr>`;
                return;
            }
            
            // Build logs rows
            let rowsHtml = "";
            data.logs.forEach(log => {
                const date = new Date(log.created_at);
                const localTime = date.toLocaleDateString() + " " + date.toLocaleTimeString();
                
                // Color badges according to incident level
                let badgeClass = "badge-ban";
                if (log.event_type.includes("KICK")) badgeClass = "badge-kick";
                else if (log.event_type.includes("CHANNEL")) badgeClass = "badge-channel";
                else if (log.event_type.includes("ROLE")) badgeClass = "badge-role";
                else if (log.event_type.includes("BOT")) badgeClass = "badge-bot";
                
                rowsHtml += `
                    <tr>
                        <td><span class="badge ${badgeClass}">${escapeHtml(log.event_type)}</span></td>
                        <td>
                            <div><strong>${escapeHtml(log.executor_tag)}</strong></div>
                            <div style="font-size: 0.75rem; color: var(--text-muted); font-family: monospace;">${escapeHtml(log.executor_id)}</div>
                        </td>
                        <td>${escapeHtml(log.action_taken)}</td>
                        <td>${escapeHtml(log.details)}</td>
                        <td style="font-family: monospace; font-size: 0.85rem; color: var(--text-muted); white-space: nowrap;">${localTime}</td>
                    </tr>
                `;
            });
            
            logsBody.innerHTML = rowsHtml;
        } catch (err) {
            logsBody.innerHTML = `<tr><td colspan="5" style="text-align: center; color: var(--c1);">Error connecting to logs server.</td></tr>`;
        }
    }
    
    // Initial load and periodic refresh (every 5 seconds)
    loadLogs();
    setInterval(loadLogs, 5000);
}

// XSS mitigation helper
function escapeHtml(str) {
    if (!str) return "";
    return str.replace(/&/g, "&amp;")
              .replace(/</g, "&lt;")
              .replace(/>/g, "&gt;")
              .replace(/"/g, "&quot;")
              .replace(/'/g, "&#039;");
}
