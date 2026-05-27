// static/js/navigationbar.js
/**
 * Kaizer K5 - Floating Rhombus Navigation Bar
 * Injects a premium, interactive floating navigation menu on the bottom right.
 */

(function() {
    // 1. Inject Stylesheet
    const style = document.createElement("style");
    style.textContent = `
        /* Floating Rhombus Button */
        .kaizer-nav-trigger {
            position: fixed;
            bottom: 30px;
            right: 30px;
            width: 52px;
            height: 52px;
            background: rgba(10, 10, 10, 0.7);
            backdrop-filter: blur(15px);
            -webkit-backdrop-filter: blur(15px);
            border: 1.5px solid var(--teal, #4ECDC4);
            cursor: pointer;
            z-index: 10000;
            display: flex;
            align-items: center;
            justify-content: center;
            transform: rotate(45deg);
            transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.4);
        }
        .kaizer-nav-trigger:hover {
            transform: rotate(45deg) scale(1.08);
            border-color: var(--orange, #FF3800);
            box-shadow: 0 0 25px rgba(78, 205, 196, 0.35);
        }
        .kaizer-nav-trigger:active {
            transform: rotate(45deg) scale(0.95);
        }
        .kaizer-nav-trigger-inner {
            transform: rotate(-45deg);
            color: #fff;
            font-size: 20px;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: transform 0.3s;
        }
        .kaizer-nav-trigger.open {
            border-color: var(--orange, #FF3800);
        }
        .kaizer-nav-trigger.open .kaizer-nav-trigger-inner {
            transform: rotate(-135deg); /* Spin animation on open */
        }

        /* Navigation Menu Container */
        .kaizer-nav-menu {
            position: fixed;
            bottom: 95px;
            right: 30px;
            background: rgba(10, 10, 10, 0.85);
            backdrop-filter: blur(25px);
            -webkit-backdrop-filter: blur(25px);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 16px;
            padding: 20px;
            display: flex;
            flex-direction: column;
            gap: 8px;
            z-index: 9999;
            transform: translateY(20px) scale(0.95);
            opacity: 0;
            pointer-events: none;
            transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
            box-shadow: 0 15px 45px rgba(0, 0, 0, 0.6);
            min-width: 230px;
        }
        .kaizer-nav-menu.open {
            transform: translateY(0) scale(1);
            opacity: 1;
            pointer-events: all;
        }

        /* User Info Section */
        .kaizer-nav-user {
            display: flex;
            align-items: center;
            gap: 12px;
            border-bottom: 1px solid rgba(255, 255, 255, 0.08);
            padding-bottom: 12px;
            margin-bottom: 8px;
        }
        .kaizer-nav-avatar {
            width: 34px;
            height: 34px;
            border-radius: 50%;
            border: 1.5px solid var(--teal, #4ECDC4);
            background: #1a1a2e;
        }
        .kaizer-nav-user-details {
            display: flex;
            flex-direction: column;
        }
        .kaizer-nav-username {
            font-size: 13px;
            font-weight: 500;
            color: #fff;
            letter-spacing: -0.01em;
            max-width: 140px;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }
        .kaizer-nav-user-tag {
            font-size: 9px;
            color: var(--teal, #4ECDC4);
            letter-spacing: 0.1em;
            text-transform: uppercase;
        }

        /* Navigation Links */
        .kaizer-nav-link {
            display: flex;
            align-items: center;
            gap: 12px;
            color: rgba(255, 255, 255, 0.55);
            text-decoration: none;
            font-size: 11px;
            font-weight: 500;
            letter-spacing: 0.15em;
            text-transform: uppercase;
            padding: 10px 14px;
            border-radius: 8px;
            transition: all 0.2s ease;
            border: 1px solid transparent;
        }
        .kaizer-nav-link:hover {
            color: #fff;
            background: rgba(255, 255, 255, 0.04);
            border-color: rgba(255, 255, 255, 0.05);
        }
        .kaizer-nav-link.active {
            color: var(--teal, #4ECDC4);
            background: rgba(78, 205, 196, 0.08);
            border-color: rgba(78, 205, 196, 0.15);
            font-weight: 600;
        }
        .kaizer-nav-link-icon {
            font-size: 12px;
            color: var(--teal, #4ECDC4);
            width: 14px;
            text-align: center;
        }
        .kaizer-nav-link.active .kaizer-nav-link-icon {
            color: var(--orange, #FF3800);
        }
    `;
    document.head.appendChild(style);

    // 2. Setup DOM Elements on Load
    function initNavigation() {
        // Read window state
        const state = window.KAIZER_STATE || { user: null, guild_id: null, active_page: "index" };
        const user = state.user;
        const guildId = state.guild_id;
        const activePage = state.active_page;

        // Create Trigger Button
        const trigger = document.createElement("div");
        trigger.className = "kaizer-nav-trigger";
        trigger.innerHTML = `<div class="kaizer-nav-trigger-inner">◈</div>`;
        document.body.appendChild(trigger);

        // Create Menu Container
        const menu = document.createElement("div");
        menu.className = "kaizer-nav-menu";
        document.body.appendChild(menu);

        // Populate User Profiling
        if (user) {
            const userSection = document.createElement("div");
            userSection.className = "kaizer-nav-user";
            
            const avatarUrl = user.avatar 
                ? `https://cdn.discordapp.com/avatars/${user.id}/${user.avatar}.png`
                : "data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='100' height='100' fill='%234ECDC4'><circle cx='50' cy='50' r='40'/></svg>";
                
            userSection.innerHTML = `
                <img src="${avatarUrl}" class="kaizer-nav-avatar" alt="Avatar">
                <div class="kaizer-nav-user-details">
                    <span class="kaizer-nav-username">${user.username}</span>
                    <span class="kaizer-nav-user-tag">AUTHORIZED</span>
                </div>
            `;
            menu.appendChild(userSection);
        }

        // Helper to add links
        function addLink(text, url, iconCode, pageKey) {
            const a = document.createElement("a");
            a.href = url;
            a.className = `kaizer-nav-link ${activePage === pageKey ? 'active' : ''}`;
            a.innerHTML = `<span class="kaizer-nav-link-icon">${iconCode}</span><span>${text}</span>`;
            menu.appendChild(a);
        }

        // Add Links logically
        addLink("Home", "/", "◆", "index");
        
        if (user) {
            addLink("Dashboard", "/dashboard", "⬡", "dashboard");
            if (guildId) {
                addLink("Server Config", `/dashboard/${guildId}`, "◈", "server");
            }
            addLink("Security Logs", "/logs", "◉", "logs");
        }
        
        addLink("Help Center", "/help", "◎", "help");

        // Add login/logout action
        if (user) {
            addLink("Logout", "/logout", "☱", "logout");
        } else {
            addLink("Login Discord", "/login", "☲", "login");
        }

        // Toggle Event
        let isOpen = false;
        function toggle() {
            isOpen = !isOpen;
            trigger.classList.toggle("open", isOpen);
            menu.classList.toggle("open", isOpen);
        }

        trigger.addEventListener("click", function(e) {
            e.stopPropagation();
            toggle();
        });

        // Close when clicking outside
        document.addEventListener("click", function(e) {
            if (isOpen && !menu.contains(e.target) && !trigger.contains(e.target)) {
                toggle();
            }
        });
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", initNavigation);
    } else {
        initNavigation();
    }
})();
