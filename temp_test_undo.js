
    // ── WELCOME & GOODBYE DASHBOARD CONFIGURATION HELPERS ────────────────────────────────────
    const WELCOME_THEMES = {
      cyan_neon: { primary: "#0affe4", secondary: "#0055ff" },
      red_hot: { primary: "#ef4444", secondary: "#991b1b" },
      emerald_green: { primary: "#10b981", secondary: "#064e3b" },
      golden_hour: { primary: "#fbbf24", secondary: "#b45309" },
      electric_purple: { primary: "#a855f7", secondary: "#4c1d95" },
      synthwave_pink: { primary: "#ec4899", secondary: "#500724" },
      dark_space: { primary: "#1e293b", secondary: "#0f172a" },
      ice_blue: { primary: "#38bdf8", secondary: "#1e3a8a" }
    };

    function hexToRgb(hex) {
      var result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
      return result ? `${parseInt(result[1], 16)}, ${parseInt(result[2], 16)}, ${parseInt(result[3], 16)}` : "255, 255, 255";
    }

    function applyCardBackground(elementId, style, color, customUrl) {
      const el = document.getElementById(elementId);
      if (!el) return;
      
      if (customUrl) {
        el.style.backgroundImage = `url('${customUrl}')`;
        el.style.backgroundSize = "cover";
        el.style.backgroundPosition = "center";
        el.style.backgroundRepeat = "no-repeat";
        return;
      }
      
      const theme = WELCOME_THEMES[color] || WELCOME_THEMES["dark_space"];
      const c1 = theme.primary;
      const c2 = theme.secondary;
      
      el.style.setProperty('--preview-primary', c1);
      
      // Clear previous styles
      el.style.backgroundRepeat = "no-repeat";
      el.style.backgroundPosition = "center";
      el.style.backgroundSize = "auto";
      
      const gradient = `linear-gradient(135deg, ${c1}, ${c2})`;
      
      if (style === "plain_gradient") {
        el.style.backgroundImage = gradient;
      } else if (style === "tech_grid") {
        el.style.backgroundImage = `linear-gradient(rgba(255,255,255,0.06) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.06) 1px, transparent 1px), ${gradient}`;
        el.style.backgroundSize = "20px 20px, 20px 20px, auto";
      } else if (style === "cosmic_stars") {
        el.style.backgroundImage = `radial-gradient(circle at 20% 30%, rgba(255,255,255,0.8) 1.5px, transparent 2px), radial-gradient(circle at 75% 60%, rgba(255,255,255,0.6) 2px, transparent 3px), radial-gradient(circle at 40% 80%, rgba(255,255,255,0.7) 1px, transparent 2.5px), ${gradient}`;
        el.style.backgroundSize = "100px 100px, 120px 120px, 80px 80px, auto";
      } else if (style === "geometric_wires") {
        el.style.backgroundImage = `repeating-linear-gradient(45deg, rgba(255,255,255,0.02) 0px, rgba(255,255,255,0.02) 1px, transparent 1px, transparent 8px), ${gradient}`;
      } else if (style === "wave_lines") {
        el.style.backgroundImage = `repeating-radial-gradient(circle at 50% 100%, transparent, transparent 40px, rgba(255,255,255,0.03) 40px, rgba(255,255,255,0.03) 80px), ${gradient}`;
      } else if (style === "circular_aura") {
        el.style.backgroundImage = `radial-gradient(circle at center 140px, rgba(255,255,255,0.2) 0%, transparent 65%), ${gradient}`;
      } else if (style === "circuit_board") {
        el.style.backgroundImage = `linear-gradient(45deg, rgba(255,255,255,0.04) 25%, transparent 25%), linear-gradient(-45deg, rgba(255,255,255,0.04) 25%, transparent 25%), ${gradient}`;
        el.style.backgroundSize = "30px 30px, 30px 30px, auto";
      } else if (style === "retro_synthwave") {
        el.style.backgroundImage = `radial-gradient(circle at center 115px, #f43f5e 40px, transparent 41px), linear-gradient(rgba(255, 45, 85, 0.15) 1px, transparent 1px), linear-gradient(90deg, rgba(255, 45, 85, 0.15) 1px, transparent 1px), linear-gradient(to bottom, #070707 55%, #1e1b4b), ${gradient}`;
        el.style.backgroundSize = "auto, 20px 20px, 20px 20px, auto, auto";
      } else if (style === "minimalist_frame") {
        el.style.backgroundImage = `linear-gradient(to right, rgba(255,255,255,0.05) 1.5px, transparent 1.5px), linear-gradient(to bottom, rgba(255,255,255,0.05) 1.5px, transparent 1.5px), ${gradient}`;
        el.style.backgroundSize = "calc(100% - 30px) 100%, 100% calc(100% - 30px), auto";
        el.style.backgroundPosition = "center center";
        el.style.backgroundRepeat = "no-repeat";
      } else if (style === "abstract_splatter") {
        el.style.backgroundImage = `radial-gradient(circle at 35% 30%, rgba(${hexToRgb(c1)}, 0.45) 0%, transparent 50%), radial-gradient(circle at 65% 70%, rgba(${hexToRgb(c2)}, 0.35) 0%, transparent 55%), ${gradient}`;
      }
    }

    function renderPresetsGrid(prefix) {
      const grid = document.getElementById(`${prefix}_presets_grid`);
      if (!grid) return;
      
      grid.innerHTML = "";
      const styles = [
        { id: "plain_gradient", name: "Plain Gradient" },
        { id: "tech_grid", name: "Tech Grid" },
        { id: "cosmic_stars", name: "Cosmic Stars" },
        { id: "geometric_wires", name: "Geometric Wires" },
        { id: "wave_lines", name: "Wave Lines" },
        { id: "circular_aura", name: "Circular Aura" },
        { id: "circuit_board", name: "Circuit Board" },
        { id: "retro_synthwave", name: "Retro Synthwave" },
        { id: "minimalist_frame", name: "Minimalist Frame" },
        { id: "abstract_splatter", name: "Abstract Splatter" }
      ];
      const colors = [
        { id: "cyan_neon", name: "Cyan" },
        { id: "red_hot", name: "Red" },
        { id: "emerald_green", name: "Green" },
        { id: "golden_hour", name: "Gold" },
        { id: "electric_purple", name: "Purple" },
        { id: "synthwave_pink", name: "Pink" },
        { id: "dark_space", name: "Dark" },
        { id: "ice_blue", name: "Ice" }
      ];
      
      styles.forEach(style => {
        colors.forEach(color => {
          const btn = document.createElement("div");
          btn.className = "preset-btn";
          btn.title = `${style.name} (${color.name})`;
          btn.dataset.style = style.id;
          btn.dataset.color = color.id;
          
          const theme = WELCOME_THEMES[color.id];
          btn.style.background = `linear-gradient(135deg, ${theme.primary}, ${theme.secondary})`;
          
          btn.onclick = () => {
            document.getElementById(`${prefix}_image_style`).value = style.id;
            document.getElementById(`${prefix}_image_color`).value = color.id;
            
            grid.querySelectorAll('.preset-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            
            if (prefix === 'welcome') updateWelcomeCardPreview();
            else updateGoodbyeCardPreview();
          };
          grid.appendChild(btn);
        });
      });
    }

    function copyPlaceholder(placeholder) {
      navigator.clipboard.writeText(placeholder);
      showToast(`Copied ${placeholder} to clipboard!`, 'success');
    }

    function toggleWelcomeFields() {
      const enabled = document.getElementById('welcome_enabled').checked;
      const container = document.getElementById('welcome_fields_container');
      if (enabled) {
        container.classList.remove('disabled-panel');
      } else {
        container.classList.add('disabled-panel');
      }
      updateWelcomeAlertPreview();
    }

    function toggleWelcomeEmbedEditor() {
      const embedEnabled = document.getElementById('welcome_embed_enabled').checked;
      const textGroup = document.getElementById('welcome_text_message_group');
      const embedEditor = document.getElementById('welcome_embed_editor');
      
      if (embedEnabled) {
        textGroup.classList.add('disabled-panel');
        embedEditor.classList.remove('disabled-panel');
      } else {
        textGroup.classList.remove('disabled-panel');
        embedEditor.classList.add('disabled-panel');
      }
      updateWelcomeAlertPreview();
    }

    function syncWelcomeEmbedColorPicker(val) {
      document.getElementById('welcome_embed_color_hex').value = val;
      updateWelcomeEmbedPreview();
    }

    function syncWelcomeEmbedColorHex(val) {
      if (/^#[0-9A-F]{6}$/i.test(val)) {
        document.getElementById('welcome_embed_color').value = val;
        updateWelcomeEmbedPreview();
      }
    }

    function updateWelcomeEmbedPreview() {
      const title = document.getElementById('welcome_embed_title').value;
      const desc = document.getElementById('welcome_embed_desc').value;
      const color = document.getElementById('welcome_embed_color_hex').value || '#0affe4';
      const thumbnail = document.getElementById('welcome_embed_thumbnail').value;
      const image = document.getElementById('welcome_embed_image').value;
      const footerText = document.getElementById('welcome_embed_footer').value;
      const footerIcon = document.getElementById('welcome_embed_footer_icon').value;
      
      const userVal = (window.KAIZER_STATE && window.KAIZER_STATE.user) ? `@${window.KAIZER_STATE.user.username}` : '@MemberName';
      const usernameVal = (window.KAIZER_STATE && window.KAIZER_STATE.user) ? window.KAIZER_STATE.user.username : 'MemberName';
      const serverVal = (window.KAIZER_STATE && window.KAIZER_STATE.guild_name) ? window.KAIZER_STATE.guild_name : 'Kaizer Server';
      
      const formatText = (txt) => {
        return txt
          .replace(/{user}/g, `<span class="discord-mention">${userVal}</span>`)
          .replace(/{username}/g, usernameVal)
          .replace(/{server}/g, serverVal)
          .replace(/{member_count}/g, '1,234')
          .replace(/{avatar_url}/g, 'https://cdn.discordapp.com/embed/avatars/0.png');
      };

      document.getElementById('welcome_embed_preview_box').style.borderColor = color;
      
      const titleEl = document.getElementById('welcome_preview_title');
      if (title) {
        titleEl.innerText = title
          .replace(/{user}/g, `@${usernameVal}`)
          .replace(/{username}/g, usernameVal)
          .replace(/{server}/g, serverVal)
          .replace(/{member_count}/g, '1,234');
        titleEl.style.display = 'block';
      } else {
        titleEl.style.display = 'none';
      }
      
      const descEl = document.getElementById('welcome_preview_desc');
      if (desc) {
        descEl.innerHTML = formatText(desc);
        descEl.style.display = 'block';
      } else {
        descEl.style.display = 'none';
      }
      
      const thumbWrapper = document.getElementById('welcome_preview_thumbnail_wrapper');
      const thumbImg = document.getElementById('welcome_preview_thumbnail');
      if (thumbnail) {
        thumbImg.src = (thumbnail === '{avatar_url}') ? 'https://cdn.discordapp.com/embed/avatars/0.png' : thumbnail;
        thumbWrapper.style.display = 'block';
      } else {
        thumbWrapper.style.display = 'none';
      }
      
      const imgWrapper = document.getElementById('welcome_preview_image_wrapper');
      const img = document.getElementById('welcome_preview_image');
      if (image) {
        img.src = image;
        imgWrapper.style.display = 'block';
      } else {
        imgWrapper.style.display = 'none';
      }
      
      const footerWrapper = document.getElementById('welcome_preview_footer_wrapper');
      const footerIconEl = document.getElementById('welcome_preview_footer_icon');
      const footerTextEl = document.getElementById('welcome_preview_footer_text');
      
      if (footerText || footerIcon) {
        footerTextEl.innerText = footerText
          .replace(/{user}/g, `@${usernameVal}`)
          .replace(/{username}/g, usernameVal)
          .replace(/{server}/g, serverVal)
          .replace(/{member_count}/g, '1,234') || '';
        if (footerIcon) {
          footerIconEl.src = footerIcon;
          footerIconEl.style.display = 'block';
        } else {
          footerIconEl.style.display = 'none';
        }
        footerWrapper.style.display = 'flex';
      } else {
        footerWrapper.style.display = 'none';
      }
    }

    // Image and DM toggles (Welcome)
    function toggleWelcomeImageFields() {
      const enabled = document.getElementById('welcome_image_enabled').checked;
      const box = document.getElementById('welcome_image_customizer_box');
      if (enabled) {
        box.classList.remove('disabled-panel');
      } else {
        box.classList.add('disabled-panel');
      }
      updateWelcomeAlertPreview();
    }

    function toggleWelcomeDMFields() {
      const enabled = document.getElementById('welcome_dm_enabled').checked;
      const box = document.getElementById('welcome_dm_customizer_box');
      if (enabled) {
        box.classList.remove('disabled-panel');
      } else {
        box.classList.add('disabled-panel');
      }
      updateWelcomeDMPreview();
    }

    function toggleWelcomeDMEmbedEditor() {
      const embedEnabled = document.getElementById('welcome_dm_embed_enabled').checked;
      const textGroup = document.getElementById('welcome_dm_text_group');
      const embedEditor = document.getElementById('welcome_dm_embed_editor');
      
      if (embedEnabled) {
        textGroup.classList.add('disabled-panel');
        embedEditor.classList.remove('disabled-panel');
      } else {
        textGroup.classList.remove('disabled-panel');
        embedEditor.classList.add('disabled-panel');
      }
      updateWelcomeDMPreview();
    }

    function updateWelcomeAlertPreview() {
      const textPreview = document.getElementById('welcome_preview_plain_text');
      const embedEnabled = document.getElementById('welcome_embed_enabled').checked;
      
      const userVal = (window.KAIZER_STATE && window.KAIZER_STATE.user) ? `@${window.KAIZER_STATE.user.username}` : '@MemberName';
      const usernameVal = (window.KAIZER_STATE && window.KAIZER_STATE.user) ? window.KAIZER_STATE.user.username : 'MemberName';
      const serverVal = (window.KAIZER_STATE && window.KAIZER_STATE.guild_name) ? window.KAIZER_STATE.guild_name : 'Kaizer Server';
      
      const formatText = (txt) => {
        return txt
          .replace(/{user}/g, `<span class="discord-mention">${userVal}</span>`)
          .replace(/{username}/g, usernameVal)
          .replace(/{server}/g, serverVal)
          .replace(/{member_count}/g, '1,234')
          .replace(/{avatar_url}/g, 'https://cdn.discordapp.com/embed/avatars/0.png');
      };

      if (embedEnabled) {
        textPreview.style.display = 'none';
        document.getElementById('welcome_embed_preview_box').style.display = 'block';
        updateWelcomeEmbedPreview();
      } else {
        textPreview.innerHTML = formatText(document.getElementById('welcome_message').value || '');
        textPreview.style.display = 'block';
        document.getElementById('welcome_embed_preview_box').style.display = 'none';
      }

      const imageEnabled = document.getElementById('welcome_image_enabled').checked;
      const cardWrapper = document.getElementById('welcome_preview_image_card_wrapper');
      if (imageEnabled) {
        cardWrapper.style.display = 'block';
        updateWelcomeCardPreview();
      } else {
        cardWrapper.style.display = 'none';
      }
    }

    function updateWelcomeCardPreview() {
      const style = document.getElementById('welcome_image_style').value;
      const color = document.getElementById('welcome_image_color').value;
      const customUrl = document.getElementById('welcome_custom_bg_url').value;
      
      const showAvatar = document.getElementById('welcome_image_show_avatar').checked;
      const showUsername = document.getElementById('welcome_image_show_username').checked;
      const showServer = document.getElementById('welcome_image_show_server').checked;
      const showCount = document.getElementById('welcome_image_show_count').checked;
      const customText = document.getElementById('welcome_image_custom_text').value;
      
      const usernameVal = (window.KAIZER_STATE && window.KAIZER_STATE.user) ? window.KAIZER_STATE.user.username : 'MemberName';
      const serverVal = (window.KAIZER_STATE && window.KAIZER_STATE.guild_name) ? window.KAIZER_STATE.guild_name : 'Kaizer Server';
      
      const formatText = (txt) => {
        return txt
          .replace(/{user}/g, `@${usernameVal}`)
          .replace(/{username}/g, usernameVal)
          .replace(/{server}/g, serverVal)
          .replace(/{member_count}/g, '1,234');
      };
      
      // Chat Preview Card
      applyCardBackground('welcome_card_preview_chat', style, color, customUrl);
      const chatAvatar = document.getElementById('welcome_card_avatar_wrapper_chat');
      if (chatAvatar) chatAvatar.style.display = showAvatar ? 'block' : 'none';
      
      const chatName = document.getElementById('welcome_card_username_chat');
      if (chatName) {
        chatName.innerText = usernameVal;
        chatName.style.display = showUsername ? 'block' : 'none';
      }
      const chatServer = document.getElementById('welcome_card_server_chat');
      if (chatServer) {
        chatServer.innerText = `Welcome to ${serverVal}`;
        chatServer.style.display = showServer ? 'block' : 'none';
      }
      const chatCount = document.getElementById('welcome_card_count_chat');
      if (chatCount) {
        chatCount.innerText = `Member #1,234`;
        chatCount.style.display = showCount ? 'block' : 'none';
      }
      const chatCustom = document.getElementById('welcome_card_custom_chat');
      if (chatCustom) {
        chatCustom.innerText = formatText(customText);
        chatCustom.style.display = customText ? 'block' : 'none';
      }

      // Editor Preview Card
      applyCardBackground('welcome_card_preview_editor', style, color, customUrl);
      const editorAvatar = document.getElementById('welcome_card_avatar_wrapper_editor');
      if (editorAvatar) editorAvatar.style.display = showAvatar ? 'block' : 'none';
      
      const editorName = document.getElementById('welcome_card_username_editor');
      if (editorName) {
        editorName.innerText = usernameVal;
        editorName.style.display = showUsername ? 'block' : 'none';
      }
      const editorServer = document.getElementById('welcome_card_server_editor');
      if (editorServer) {
        editorServer.innerText = `Welcome to ${serverVal}`;
        editorServer.style.display = showServer ? 'block' : 'none';
      }
      const editorCount = document.getElementById('welcome_card_count_editor');
      if (editorCount) {
        editorCount.innerText = `Member #1,234`;
        editorCount.style.display = showCount ? 'block' : 'none';
      }
      const editorCustom = document.getElementById('welcome_card_custom_editor');
      if (editorCustom) {
        editorCustom.innerText = formatText(customText);
        editorCustom.style.display = customText ? 'block' : 'none';
      }
    }

    function updateWelcomeDMPreview() {
      const embedEnabled = document.getElementById('welcome_dm_embed_enabled').checked;
      const textPreview = document.getElementById('welcome_dm_preview_text');
      const embedBox = document.getElementById('welcome_dm_embed_preview_box');
      
      const userVal = (window.KAIZER_STATE && window.KAIZER_STATE.user) ? `@${window.KAIZER_STATE.user.username}` : '@MemberName';
      const usernameVal = (window.KAIZER_STATE && window.KAIZER_STATE.user) ? window.KAIZER_STATE.user.username : 'MemberName';
      const serverVal = (window.KAIZER_STATE && window.KAIZER_STATE.guild_name) ? window.KAIZER_STATE.guild_name : 'Kaizer Server';
      
      const formatText = (txt) => {
        return txt
          .replace(/{user}/g, `<span class="discord-mention">${userVal}</span>`)
          .replace(/{username}/g, usernameVal)
          .replace(/{server}/g, serverVal)
          .replace(/{member_count}/g, '1,234')
          .replace(/{avatar_url}/g, 'https://cdn.discordapp.com/embed/avatars/0.png');
      };

      if (embedEnabled) {
        textPreview.style.display = 'none';
        embedBox.style.display = 'block';
        
        const title = document.getElementById('welcome_dm_embed_title').value;
        const desc = document.getElementById('welcome_dm_embed_desc').value;
        const color = document.getElementById('welcome_dm_embed_color_hex').value || '#0affe4';
        const thumbnail = document.getElementById('welcome_dm_embed_thumbnail').value;
        const image = document.getElementById('welcome_dm_embed_image').value;
        const footerText = document.getElementById('welcome_dm_embed_footer').value;
        const footerIcon = document.getElementById('welcome_dm_embed_footer_icon').value;
        
        embedBox.style.borderColor = color;
        
        const titleEl = document.getElementById('welcome_dm_preview_title');
        if (title) {
          titleEl.innerText = title
            .replace(/{user}/g, `@${usernameVal}`)
            .replace(/{username}/g, usernameVal)
            .replace(/{server}/g, serverVal)
            .replace(/{member_count}/g, '1,234');
          titleEl.style.display = 'block';
        } else {
          titleEl.style.display = 'none';
        }
        
        const descEl = document.getElementById('welcome_dm_preview_desc');
        if (desc) {
          descEl.innerHTML = formatText(desc);
          descEl.style.display = 'block';
        } else {
          descEl.style.display = 'none';
        }
        
        const thumbWrapper = document.getElementById('welcome_dm_preview_thumbnail_wrapper');
        const thumbImg = document.getElementById('welcome_dm_preview_thumbnail');
        if (thumbnail) {
          thumbImg.src = (thumbnail === '{avatar_url}') ? 'https://cdn.discordapp.com/embed/avatars/0.png' : thumbnail;
          thumbWrapper.style.display = 'block';
        } else {
          thumbWrapper.style.display = 'none';
        }
        
        const imgWrapper = document.getElementById('welcome_dm_preview_image_wrapper');
        const img = document.getElementById('welcome_dm_preview_image');
        if (image) {
          img.src = image;
          imgWrapper.style.display = 'block';
        } else {
          imgWrapper.style.display = 'none';
        }
        
        const footerWrapper = document.getElementById('welcome_dm_preview_footer_wrapper');
        const footerIconEl = document.getElementById('welcome_dm_preview_footer_icon');
        const footerTextEl = document.getElementById('welcome_dm_preview_footer_text');
        
        if (footerText || footerIcon) {
          footerTextEl.innerText = footerText
            .replace(/{user}/g, `@${usernameVal}`)
            .replace(/{username}/g, usernameVal)
            .replace(/{server}/g, serverVal)
            .replace(/{member_count}/g, '1,234') || '';
          if (footerIcon) {
            footerIconEl.src = footerIcon;
            footerIconEl.style.display = 'block';
          } else {
            footerIconEl.style.display = 'none';
          }
          footerWrapper.style.display = 'flex';
        } else {
          footerWrapper.style.display = 'none';
        }
      } else {
        textPreview.innerHTML = formatText(document.getElementById('welcome_dm_text').value || '');
        textPreview.style.display = 'block';
        embedBox.style.display = 'none';
      }
    }


    // Goodbye toggles
    function toggleGoodbyeFields() {
      const enabled = document.getElementById('goodbye_enabled').checked;
      const container = document.getElementById('goodbye_fields_container');
      if (enabled) {
        container.classList.remove('disabled-panel');
      } else {
        container.classList.add('disabled-panel');
      }
      updateGoodbyeAlertPreview();
    }

    function toggleGoodbyeEmbedEditor() {
      const embedEnabled = document.getElementById('goodbye_embed_enabled').checked;
      const textGroup = document.getElementById('goodbye_text_message_group');
      const embedEditor = document.getElementById('goodbye_embed_editor');
      
      if (embedEnabled) {
        textGroup.classList.add('disabled-panel');
        embedEditor.classList.remove('disabled-panel');
      } else {
        textGroup.classList.remove('disabled-panel');
        embedEditor.classList.add('disabled-panel');
      }
      updateGoodbyeAlertPreview();
    }

    function syncGoodbyeEmbedColorPicker(val) {
      document.getElementById('goodbye_embed_color_hex').value = val;
      updateGoodbyeEmbedPreview();
    }

    function syncGoodbyeEmbedColorHex(val) {
      if (/^#[0-9A-F]{6}$/i.test(val)) {
        document.getElementById('goodbye_embed_color').value = val;
        updateGoodbyeEmbedPreview();
      }
    }

    function updateGoodbyeEmbedPreview() {
      const title = document.getElementById('goodbye_embed_title').value;
      const desc = document.getElementById('goodbye_embed_desc').value;
      const color = document.getElementById('goodbye_embed_color_hex').value || '#ef4444';
      const thumbnail = document.getElementById('goodbye_embed_thumbnail').value;
      const image = document.getElementById('goodbye_embed_image').value;
      const footerText = document.getElementById('goodbye_embed_footer').value;
      const footerIcon = document.getElementById('goodbye_embed_footer_icon').value;
      
      const userVal = (window.KAIZER_STATE && window.KAIZER_STATE.user) ? `@${window.KAIZER_STATE.user.username}` : '@MemberName';
      const usernameVal = (window.KAIZER_STATE && window.KAIZER_STATE.user) ? window.KAIZER_STATE.user.username : 'MemberName';
      const serverVal = (window.KAIZER_STATE && window.KAIZER_STATE.guild_name) ? window.KAIZER_STATE.guild_name : 'Kaizer Server';
      
      const formatText = (txt) => {
        return txt
          .replace(/{user}/g, `<span class="discord-mention">${userVal}</span>`)
          .replace(/{username}/g, usernameVal)
          .replace(/{server}/g, serverVal)
          .replace(/{member_count}/g, '1,234')
          .replace(/{avatar_url}/g, 'https://cdn.discordapp.com/embed/avatars/0.png');
      };

      document.getElementById('goodbye_embed_preview_box').style.borderColor = color;
      
      const titleEl = document.getElementById('goodbye_preview_title');
      if (title) {
        titleEl.innerText = title
          .replace(/{user}/g, `@${usernameVal}`)
          .replace(/{username}/g, usernameVal)
          .replace(/{server}/g, serverVal)
          .replace(/{member_count}/g, '1,234');
        titleEl.style.display = 'block';
      } else {
        titleEl.style.display = 'none';
      }
      
      const descEl = document.getElementById('goodbye_preview_desc');
      if (desc) {
        descEl.innerHTML = formatText(desc);
        descEl.style.display = 'block';
      } else {
        descEl.style.display = 'none';
      }
      
      const thumbWrapper = document.getElementById('goodbye_preview_thumbnail_wrapper');
      const thumbImg = document.getElementById('goodbye_preview_thumbnail');
      if (thumbnail) {
        thumbImg.src = (thumbnail === '{avatar_url}') ? 'https://cdn.discordapp.com/embed/avatars/0.png' : thumbnail;
        thumbWrapper.style.display = 'block';
      } else {
        thumbWrapper.style.display = 'none';
      }
      
      const imgWrapper = document.getElementById('goodbye_preview_image_wrapper');
      const img = document.getElementById('goodbye_preview_image');
      if (image) {
        img.src = image;
        imgWrapper.style.display = 'block';
      } else {
        imgWrapper.style.display = 'none';
      }
      
      const footerWrapper = document.getElementById('goodbye_preview_footer_wrapper');
      const footerIconEl = document.getElementById('goodbye_preview_footer_icon');
      const footerTextEl = document.getElementById('goodbye_preview_footer_text');
      
      if (footerText || footerIcon) {
        footerTextEl.innerText = footerText
          .replace(/{user}/g, `@${usernameVal}`)
          .replace(/{username}/g, usernameVal)
          .replace(/{server}/g, serverVal)
          .replace(/{member_count}/g, '1,234') || '';
        if (footerIcon) {
          footerIconEl.src = footerIcon;
          footerIconEl.style.display = 'block';
        } else {
          footerIconEl.style.display = 'none';
        }
        footerWrapper.style.display = 'flex';
      } else {
        footerWrapper.style.display = 'none';
      }
    }

    // Image and DM toggles (Goodbye)
    function toggleGoodbyeImageFields() {
      const enabled = document.getElementById('goodbye_image_enabled').checked;
      const box = document.getElementById('goodbye_image_customizer_box');
      if (enabled) {
        box.classList.remove('disabled-panel');
      } else {
        box.classList.add('disabled-panel');
      }
      updateGoodbyeAlertPreview();
    }

    function toggleGoodbyeDMFields() {
      const enabled = document.getElementById('goodbye_dm_enabled').checked;
      const box = document.getElementById('goodbye_dm_customizer_box');
      if (enabled) {
        box.classList.remove('disabled-panel');
      } else {
        box.classList.add('disabled-panel');
      }
      updateGoodbyeDMPreview();
    }

    function toggleGoodbyeDMEmbedEditor() {
      const embedEnabled = document.getElementById('goodbye_dm_embed_enabled').checked;
      const textGroup = document.getElementById('goodbye_dm_text_group');
      const embedEditor = document.getElementById('goodbye_dm_embed_editor');
      
      if (embedEnabled) {
        textGroup.classList.add('disabled-panel');
        embedEditor.classList.remove('disabled-panel');
      } else {
        textGroup.classList.remove('disabled-panel');
        embedEditor.classList.add('disabled-panel');
      }
      updateGoodbyeDMPreview();
    }

    function updateGoodbyeAlertPreview() {
      const textPreview = document.getElementById('goodbye_preview_plain_text');
      const embedEnabled = document.getElementById('goodbye_embed_enabled').checked;
      
      const userVal = (window.KAIZER_STATE && window.KAIZER_STATE.user) ? `@${window.KAIZER_STATE.user.username}` : '@MemberName';
      const usernameVal = (window.KAIZER_STATE && window.KAIZER_STATE.user) ? window.KAIZER_STATE.user.username : 'MemberName';
      const serverVal = (window.KAIZER_STATE && window.KAIZER_STATE.guild_name) ? window.KAIZER_STATE.guild_name : 'Kaizer Server';
      
      const formatText = (txt) => {
        return txt
          .replace(/{user}/g, `<span class="discord-mention">${userVal}</span>`)
          .replace(/{username}/g, usernameVal)
          .replace(/{server}/g, serverVal)
          .replace(/{member_count}/g, '1,234')
          .replace(/{avatar_url}/g, 'https://cdn.discordapp.com/embed/avatars/0.png');
      };

      if (embedEnabled) {
        textPreview.style.display = 'none';
        document.getElementById('goodbye_embed_preview_box').style.display = 'block';
        updateGoodbyeEmbedPreview();
      } else {
        textPreview.innerHTML = formatText(document.getElementById('goodbye_message').value || '');
        textPreview.style.display = 'block';
        document.getElementById('goodbye_embed_preview_box').style.display = 'none';
      }

      const imageEnabled = document.getElementById('goodbye_image_enabled').checked;
      const cardWrapper = document.getElementById('goodbye_preview_image_card_wrapper');
      if (imageEnabled) {
        cardWrapper.style.display = 'block';
        updateGoodbyeCardPreview();
      } else {
        cardWrapper.style.display = 'none';
      }
    }

    function updateGoodbyeCardPreview() {
      const style = document.getElementById('goodbye_image_style').value;
      const color = document.getElementById('goodbye_image_color').value;
      const customUrl = document.getElementById('goodbye_custom_bg_url').value;
      
      const showAvatar = document.getElementById('goodbye_image_show_avatar').checked;
      const showUsername = document.getElementById('goodbye_image_show_username').checked;
      const showServer = document.getElementById('goodbye_image_show_server').checked;
      const showCount = document.getElementById('goodbye_image_show_count').checked;
      const customText = document.getElementById('goodbye_image_custom_text').value;
      
      const usernameVal = (window.KAIZER_STATE && window.KAIZER_STATE.user) ? window.KAIZER_STATE.user.username : 'MemberName';
      const serverVal = (window.KAIZER_STATE && window.KAIZER_STATE.guild_name) ? window.KAIZER_STATE.guild_name : 'Kaizer Server';
      
      const formatText = (txt) => {
        return txt
          .replace(/{user}/g, `@${usernameVal}`)
          .replace(/{username}/g, usernameVal)
          .replace(/{server}/g, serverVal)
          .replace(/{member_count}/g, '1,234');
      };
      
      // Chat Preview Card
      applyCardBackground('goodbye_card_preview_chat', style, color, customUrl);
      const chatAvatar = document.getElementById('goodbye_card_avatar_wrapper_chat');
      if (chatAvatar) chatAvatar.style.display = showAvatar ? 'block' : 'none';
      
      const chatName = document.getElementById('goodbye_card_username_chat');
      if (chatName) {
        chatName.innerText = usernameVal;
        chatName.style.display = showUsername ? 'block' : 'none';
      }
      const chatServer = document.getElementById('goodbye_card_server_chat');
      if (chatServer) {
        chatServer.innerText = `Goodbye from ${serverVal}`;
        chatServer.style.display = showServer ? 'block' : 'none';
      }
      const chatCount = document.getElementById('goodbye_card_count_chat');
      if (chatCount) {
        chatCount.innerText = `Member #1,234`;
        chatCount.style.display = showCount ? 'block' : 'none';
      }
      const chatCustom = document.getElementById('goodbye_card_custom_chat');
      if (chatCustom) {
        chatCustom.innerText = formatText(customText);
        chatCustom.style.display = customText ? 'block' : 'none';
      }

      // Editor Preview Card
      applyCardBackground('goodbye_card_preview_editor', style, color, customUrl);
      const editorAvatar = document.getElementById('goodbye_card_avatar_wrapper_editor');
      if (editorAvatar) editorAvatar.style.display = showAvatar ? 'block' : 'none';
      
      const editorName = document.getElementById('goodbye_card_username_editor');
      if (editorName) {
        editorName.innerText = usernameVal;
        editorName.style.display = showUsername ? 'block' : 'none';
      }
      const editorServer = document.getElementById('goodbye_card_server_editor');
      if (editorServer) {
        editorServer.innerText = `Goodbye from ${serverVal}`;
        editorServer.style.display = showServer ? 'block' : 'none';
      }
      const editorCount = document.getElementById('goodbye_card_count_editor');
      if (editorCount) {
        editorCount.innerText = `Member #1,234`;
        editorCount.style.display = showCount ? 'block' : 'none';
      }
      const editorCustom = document.getElementById('goodbye_card_custom_editor');
      if (editorCustom) {
        editorCustom.innerText = formatText(customText);
        editorCustom.style.display = customText ? 'block' : 'none';
      }
    }

    function updateGoodbyeDMPreview() {
      const embedEnabled = document.getElementById('goodbye_dm_embed_enabled').checked;
      const textPreview = document.getElementById('goodbye_dm_preview_text');
      const embedBox = document.getElementById('goodbye_dm_embed_preview_box');
      
      const userVal = (window.KAIZER_STATE && window.KAIZER_STATE.user) ? `@${window.KAIZER_STATE.user.username}` : '@MemberName';
      const usernameVal = (window.KAIZER_STATE && window.KAIZER_STATE.user) ? window.KAIZER_STATE.user.username : 'MemberName';
      const serverVal = (window.KAIZER_STATE && window.KAIZER_STATE.guild_name) ? window.KAIZER_STATE.guild_name : 'Kaizer Server';
      
      const formatText = (txt) => {
        return txt
          .replace(/{user}/g, `<span class="discord-mention">${userVal}</span>`)
          .replace(/{username}/g, usernameVal)
          .replace(/{server}/g, serverVal)
          .replace(/{member_count}/g, '1,234')
          .replace(/{avatar_url}/g, 'https://cdn.discordapp.com/embed/avatars/0.png');
      };

      if (embedEnabled) {
        textPreview.style.display = 'none';
        embedBox.style.display = 'block';
        
        const title = document.getElementById('goodbye_dm_embed_title').value;
        const desc = document.getElementById('goodbye_dm_embed_desc').value;
        const color = document.getElementById('goodbye_dm_embed_color_hex').value || '#ef4444';
        const thumbnail = document.getElementById('goodbye_dm_embed_thumbnail').value;
        const image = document.getElementById('goodbye_dm_embed_image').value;
        const footerText = document.getElementById('goodbye_dm_embed_footer').value;
        const footerIcon = document.getElementById('goodbye_dm_embed_footer_icon').value;
        
        embedBox.style.borderColor = color;
        
        const titleEl = document.getElementById('goodbye_dm_preview_title');
        if (title) {
          titleEl.innerText = title
            .replace(/{user}/g, `@${usernameVal}`)
            .replace(/{username}/g, usernameVal)
            .replace(/{server}/g, serverVal)
            .replace(/{member_count}/g, '1,234');
          titleEl.style.display = 'block';
        } else {
          titleEl.style.display = 'none';
        }
        
        const descEl = document.getElementById('goodbye_dm_preview_desc');
        if (desc) {
          descEl.innerHTML = formatText(desc);
          descEl.style.display = 'block';
        } else {
          descEl.style.display = 'none';
        }
        
        const thumbWrapper = document.getElementById('goodbye_dm_preview_thumbnail_wrapper');
        const thumbImg = document.getElementById('goodbye_dm_preview_thumbnail');
        if (thumbnail) {
          thumbImg.src = (thumbnail === '{avatar_url}') ? 'https://cdn.discordapp.com/embed/avatars/0.png' : thumbnail;
          thumbWrapper.style.display = 'block';
        } else {
          thumbWrapper.style.display = 'none';
        }
        
        const imgWrapper = document.getElementById('goodbye_dm_preview_image_wrapper');
        const img = document.getElementById('goodbye_dm_preview_image');
        if (image) {
          img.src = image;
          imgWrapper.style.display = 'block';
        } else {
          imgWrapper.style.display = 'none';
        }
        
        const footerWrapper = document.getElementById('goodbye_dm_preview_footer_wrapper');
        const footerIconEl = document.getElementById('goodbye_dm_preview_footer_icon');
        const footerTextEl = document.getElementById('goodbye_dm_preview_footer_text');
        
        if (footerText || footerIcon) {
          footerTextEl.innerText = footerText
            .replace(/{user}/g, `@${usernameVal}`)
            .replace(/{username}/g, usernameVal)
            .replace(/{server}/g, serverVal)
            .replace(/{member_count}/g, '1,234') || '';
          if (footerIcon) {
            footerIconEl.src = footerIcon;
            footerIconEl.style.display = 'block';
          } else {
            footerIconEl.style.display = 'none';
          }
          footerWrapper.style.display = 'flex';
        } else {
          footerWrapper.style.display = 'none';
        }
      } else {
        textPreview.innerHTML = formatText(document.getElementById('goodbye_dm_text').value || '');
        textPreview.style.display = 'block';
        embedBox.style.display = 'none';
      }
    }

    async function triggerTestEvent(prefix) {
      if (typeof guildId === 'undefined') {
        showToast("Guild ID not found.", "error");
        return;
      }
      try {
        const response = await fetch(`/api/guild/${guildId}/${prefix}/test`, {
          method: "POST",
          headers: { "Content-Type": "application/json" }
        });
        const result = await response.json();
        if (response.ok && result.success) {
          showToast(result.message || `Test ${prefix.toUpperCase()} Alert triggered!`, "success");
        } else {
          showToast(result.error || `Failed to trigger test ${prefix} alert`, "error");
        }
      } catch (err) {
        showToast(`Connection error while sending test alert`, "error");
      }
    }
    
    // ── TICKET SYSTEM MANAGEMENT ─────────────────────────────────────────────
    function populateTicketsDropdowns(roles) {
      const ticketRoleSelect = document.getElementById('ticket_support_role');
      if (ticketRoleSelect) {
        const oldVal = ticketRoleSelect.value;
        ticketRoleSelect.innerHTML = '<option value="">-- Choose Support Role --</option>';
        roles.forEach(role => {
          const opt = document.createElement('option');
          opt.value = role.id;
          opt.innerText = role.name;
          ticketRoleSelect.appendChild(opt);
        });
        if (oldVal) ticketRoleSelect.value = oldVal;
      }

      const ticketCategorySelect = document.getElementById('ticket_category');
      if (ticketCategorySelect) {
        const oldVal = ticketCategorySelect.value;
        ticketCategorySelect.innerHTML = '<option value="">-- Choose Category --</option>';
        if (activeLayoutData && activeLayoutData.categories) {
          activeLayoutData.categories.forEach(cat => {
            if (cat.id !== 'none') {
              const opt = document.createElement('option');
              opt.value = cat.id;
              opt.innerText = cat.name;
              ticketCategorySelect.appendChild(opt);
            }
          });
        }
        if (oldVal) ticketCategorySelect.value = oldVal;
      }

      const ticketLogSelect = document.getElementById('ticket_log_channel');
      if (ticketLogSelect) {
        const oldVal = ticketLogSelect.value;
        ticketLogSelect.innerHTML = '<option value="">-- Choose Log Channel --</option>';
        if (activeLayoutData && activeLayoutData.categories) {
          activeLayoutData.categories.forEach(cat => {
            cat.channels.forEach(chan => {
              if (chan.type === 'text') {
                const opt = document.createElement('option');
                opt.value = chan.id;
                opt.innerText = `# ${chan.name} (${cat.name})`;
                ticketLogSelect.appendChild(opt);
              }
            });
          });
        }
        if (oldVal) ticketLogSelect.value = oldVal;
      }
    }

    async function createRoleForTicketsPrompt() {
      const name = window.prompt("Enter the name of the support role to create (if it exists, its color will be overwritten):");
      if (!name) return;
      
      try {
         showToast("Creating/Overwriting support role...", "info");
         const res = await fetch(`/api/guild/${guildId}/server-action`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ action: 'create_role', role_name: name, role_color: '#0affe4' })
         });
         const data = await res.json().catch(() => ({}));
         if (data.success && data.role) {
            showToast(`Support role "${data.role.name}" loaded successfully!`, 'success');
            
            // Check if role already exists in activeLayoutData.roles
            if (activeLayoutData) {
               if (!activeLayoutData.roles) activeLayoutData.roles = [];
               const existingIdx = activeLayoutData.roles.findIndex(r => r.id === data.role.id || r.name.toLowerCase() === data.role.name.toLowerCase());
               if (existingIdx > -1) {
                  activeLayoutData.roles[existingIdx] = data.role; // Update
               } else {
                  activeLayoutData.roles.push(data.role); // Append
               }
            }
            
            // Refresh all dropdowns
            populateTicketsDropdowns(activeLayoutData.roles);
            populateLevelingRolesDropdowns(activeLayoutData.roles);
            
            const bulkRoleSelect = document.getElementById('bulk_role_id');
            if (bulkRoleSelect) {
               // Rebuild bulk role options
               bulkRoleSelect.innerHTML = '<option value="">-- Select Role --</option>';
               activeLayoutData.roles.forEach(role => {
                  const opt = document.createElement('option');
                  opt.value = role.id;
                  opt.innerText = role.name;
                  opt.dataset.color = role.color;
                  bulkRoleSelect.appendChild(opt);
               });
            }
            
            // Select this role in the support role dropdown
            const ticketRoleSelect = document.getElementById('ticket_support_role');
            if (ticketRoleSelect) {
               ticketRoleSelect.value = data.role.id;
            }
         } else {
            showToast(data.error || 'Failed to create/load support role.', 'error');
         }
      } catch (e) {
         showToast('Network error occurred.', 'error');
      }
    }

    // ── LEVELING SYSTEM MANAGEMENT ──────────────────────────────────────────
    let currentLevelRoles = {};
    let currentLevelPermissions = [];

    function populateLevelingRolesDropdowns(roles) {
      const rewardRoleSelect = document.getElementById('level_reward_role');
      if (rewardRoleSelect) {
        if (!roles || roles.length === 0) {
          rewardRoleSelect.innerHTML = '<option value="">-- No Custom Roles Found --</option>';
        } else {
          rewardRoleSelect.innerHTML = '<option value="">-- Choose Role --</option>';
          roles.forEach(role => {
            const opt = document.createElement('option');
            opt.value = role.id;
            opt.innerText = role.name;
            rewardRoleSelect.appendChild(opt);
          });
        }
      }
    }

    function toggleCustomLevelInput(selectEl, wrapperId) {
      const wrapper = document.getElementById(wrapperId);
      if (wrapper) {
        wrapper.style.display = selectEl.value === 'custom' ? 'block' : 'none';
      }
    }

    function renderLevelRolesList() {
      const hiddenInput = document.getElementById('level_roles');
      if (hiddenInput && hiddenInput.value) {
        try {
          currentLevelRoles = typeof hiddenInput.value === 'string' ? JSON.parse(hiddenInput.value) : hiddenInput.value;
        } catch (e) {
          currentLevelRoles = {};
        }
      } else {
        currentLevelRoles = {};
      }

      const container = document.getElementById('level_roles_list');
      if (!container) return;

      container.innerHTML = '';
      const levels = Object.keys(currentLevelRoles).map(Number).sort((a, b) => a - b);

      if (levels.length === 0) {
        container.innerHTML = '<div style="color: var(--text-muted); font-size: 0.9rem; font-style: italic; padding: 10px 0;">No level role rewards configured yet.</div>';
        return;
      }

      levels.forEach(lvl => {
        const roleId = currentLevelRoles[lvl];
        const roleObj = activeLayoutData && activeLayoutData.roles ? activeLayoutData.roles.find(r => r.id === roleId) : null;
        const roleName = roleObj ? roleObj.name : `Unknown Role (ID: ${roleId})`;
        let roleColor = roleObj && roleObj.color && roleObj.color !== '#000000' ? roleObj.color : '#0affe4';
        
        // If color format is integer, convert it
        if (roleObj && typeof roleObj.color === 'string' && !roleObj.color.startsWith('#')) {
          const cInt = parseInt(roleObj.color);
          if (!isNaN(cInt)) {
            roleColor = '#' + cInt.toString(16).padStart(6, '0');
          }
        }

        const card = document.createElement('div');
        card.style.display = 'flex';
        card.style.justifyContent = 'space-between';
        card.style.alignItems = 'center';
        card.style.background = 'rgba(255, 255, 255, 0.02)';
        card.style.border = '1px solid rgba(255, 255, 255, 0.05)';
        card.style.padding = '10px 15px';
        card.style.marginBottom = '8px';
        card.style.borderRadius = '0px';
        card.style.borderLeft = `3px solid ${roleColor}`;

        card.innerHTML = `
          <div>
            <span style="font-weight: bold; color: var(--c2); font-family: monospace;">Level ${lvl}</span>
            <span style="color: var(--text-muted); margin: 0 8px;">➜</span>
            <span style="color: ${roleColor}; font-weight: 500;">${roleName}</span>
          </div>
          <button type="button" class="btn btn-secondary" style="padding: 6px 12px; font-size: 10px; border-color: var(--c1) !important; color: var(--c1) !important; line-height: 1;" onclick="removeLevelRoleReward(${lvl})">Remove</button>
        `;
        container.appendChild(card);
      });
    }

    function addLevelRoleReward() {
      const levelSelect = document.getElementById('level_reward_level');
      const customLevelInput = document.getElementById('level_reward_level_custom');
      const roleSelect = document.getElementById('level_reward_role');

      let level = parseInt(levelSelect.value);
      if (levelSelect.value === 'custom' && customLevelInput) {
        level = parseInt(customLevelInput.value);
      }

      const roleId = roleSelect.value;

      if (isNaN(level) || level <= 0) {
        showToast('Please enter/select a valid level (greater than 0).', 'error');
        return;
      }
      if (!roleId) {
        showToast('Please select a role reward.', 'error');
        return;
      }

      currentLevelRoles[level] = roleId;

      // Update hidden input
      document.getElementById('level_roles').value = JSON.stringify(currentLevelRoles);

      // Re-render
      renderLevelRolesList();
      showToast(`Added role reward for Level ${level}!`, 'success');
    }

    function removeLevelRoleReward(level) {
      delete currentLevelRoles[level];
      document.getElementById('level_roles').value = JSON.stringify(currentLevelRoles);
      renderLevelRolesList();
      showToast(`Removed role reward for Level ${level}`, 'success');
    }

    function renderLevelPermissionsList() {
      const hiddenInput = document.getElementById('level_permissions');
      if (hiddenInput && hiddenInput.value) {
        try {
          currentLevelPermissions = typeof hiddenInput.value === 'string' ? JSON.parse(hiddenInput.value) : hiddenInput.value;
          if (!Array.isArray(currentLevelPermissions)) currentLevelPermissions = [];
        } catch (e) {
          currentLevelPermissions = [];
        }
      } else {
        currentLevelPermissions = [];
      }

      const container = document.getElementById('level_permissions_list');
      if (!container) return;

      container.innerHTML = '';
      const sortedRules = [...currentLevelPermissions].sort((a, b) => a.level - b.level);

      if (sortedRules.length === 0) {
        container.innerHTML = '<div style="color: var(--text-muted); font-size: 0.9rem; font-style: italic; padding: 10px 0;">No level permission rules configured yet.</div>';
        return;
      }

      sortedRules.forEach(rule => {
        const lvl = rule.level;
        const allowText = rule.allow_text !== false;
        const allowImage = rule.allow_image !== false;
        const allowGif = rule.allow_gif !== false;

        const card = document.createElement('div');
        card.style.display = 'flex';
        card.style.justifyContent = 'space-between';
        card.style.alignItems = 'center';
        card.style.background = 'rgba(255, 255, 255, 0.02)';
        card.style.border = '1px solid rgba(255, 255, 255, 0.05)';
        card.style.padding = '10px 15px';
        card.style.marginBottom = '8px';
        card.style.borderRadius = '0px';
        card.style.borderLeft = `3px solid var(--c2)`;

        card.innerHTML = `
          <div>
            <span style="font-weight: bold; color: var(--c2); font-family: monospace;">Level ${lvl}+</span>
            <span style="color: var(--text-muted); margin: 0 8px;">➜</span>
            <span style="font-size: 0.85rem; font-family: monospace;">
              Text: ${allowText ? '<span style="color:#10b981; font-weight:bold;">YES</span>' : '<span style="color:#ef4444; font-weight:bold;">NO</span>'} | 
              Images: ${allowImage ? '<span style="color:#10b981; font-weight:bold;">YES</span>' : '<span style="color:#ef4444; font-weight:bold;">NO</span>'} | 
              GIFs: ${allowGif ? '<span style="color:#10b981; font-weight:bold;">YES</span>' : '<span style="color:#ef4444; font-weight:bold;">NO</span>'}
            </span>
          </div>
          <button type="button" class="btn btn-secondary" style="padding: 6px 12px; font-size: 10px; border-color: var(--c1) !important; color: var(--c1) !important; line-height: 1;" onclick="removeLevelPermissionRule(${lvl})">Remove</button>
        `;
        container.appendChild(card);
      });
    }

    function addLevelPermissionRule() {
      const levelSelect = document.getElementById('level_perm_level');
      const customLevelInput = document.getElementById('level_perm_level_custom');

      let level = parseInt(levelSelect.value);
      if (levelSelect.value === 'custom' && customLevelInput) {
        level = parseInt(customLevelInput.value);
      }

      if (isNaN(level) || level < 0) {
        showToast('Please enter/select a valid level threshold.', 'error');
        return;
      }
      const allowText = document.getElementById('level_perm_allow_text').checked;
      const allowImage = document.getElementById('level_perm_allow_image').checked;
      const allowGif = document.getElementById('level_perm_allow_gif').checked;

      const existingIdx = currentLevelPermissions.findIndex(r => r.level === level);
      const newRule = {
        level: level,
        allow_text: allowText,
        allow_image: allowImage,
        allow_gif: allowGif
      };

      if (existingIdx > -1) {
        currentLevelPermissions[existingIdx] = newRule;
      } else {
        currentLevelPermissions.push(newRule);
      }

      // Update hidden input
      document.getElementById('level_permissions').value = JSON.stringify(currentLevelPermissions);

      // Re-render
      renderLevelPermissionsList();
      showToast(`Added permission override for Level ${level}!`, 'success');
    }

    function removeLevelPermissionRule(level) {
      currentLevelPermissions = currentLevelPermissions.filter(r => r.level !== level);
      document.getElementById('level_permissions').value = JSON.stringify(currentLevelPermissions);
      renderLevelPermissionsList();
      showToast(`Removed permission override for Level ${level}`, 'success');
    }

    async function createRoleFromLeveling() {
      const nameInput = document.getElementById('new_role_name');
      const colorInput = document.getElementById('new_role_color');

      const roleName = nameInput.value.trim();
      const roleColor = colorInput.value; // e.g. #0affe4

      if (!roleName) {
        showToast('Please enter a role name.', 'error');
        return;
      }

      const btn = document.getElementById('btn-create-leveling-role');
      const originalText = btn.innerHTML;
      btn.innerHTML = '<span>Creating...</span>';
      btn.disabled = true;

      try {
        const res = await fetch(`/api/guild/${guildId}/server-action`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ action: 'create_role', role_name: roleName, role_color: roleColor })
        });
        const data = await res.json().catch(() => ({}));
        if (res.ok && data.success && data.role) {
          showToast(`Role "${data.role.name}" created successfully in Discord!`, 'success');
          
          nameInput.value = '';

          // Append new role to activeLayoutData
          if (activeLayoutData) {
            if (!activeLayoutData.roles) activeLayoutData.roles = [];
            activeLayoutData.roles.push(data.role);
          }

          // Re-populate all dropdowns on the page
          populateLevelingRolesDropdowns(activeLayoutData.roles);

          // Update other role dropdowns (like bulk role select)
          const bulkRoleSelect = document.getElementById('bulk_role_id');
          if (bulkRoleSelect) {
             const opt = document.createElement('option');
             opt.value = data.role.id;
             opt.innerText = data.role.name;
             opt.dataset.color = data.role.color;
             bulkRoleSelect.appendChild(opt);
          }
        } else {
          showToast(data.error || 'Failed to create role.', 'error');
        }
      } catch (e) {
        showToast('Network error occurred.', 'error');
    }

    // ── BOT SETTINGS CONFIGURATION HANDLERS ──────────────────────────────────
    let currentPrefixes = [];
    let currentAdminRoles = [];
    let currentModRoles = [];

    function populateBotSettingsRoles(roles) {
      const adminSelect = document.getElementById('admin_roles_select');
      const modSelect = document.getElementById('mod_roles_select');
      if (adminSelect) adminSelect.innerHTML = '<option value="">-- Select Role --</option>';
      if (modSelect) modSelect.innerHTML = '<option value="">-- Select Role --</option>';
      
      roles.forEach(role => {
        const opt = document.createElement('option');
        opt.value = role.id;
        opt.innerText = role.name;
        if (adminSelect) adminSelect.appendChild(opt.cloneNode(true));
        if (modSelect) modSelect.appendChild(opt.cloneNode(true));
      });
    }

    // Prefix list builders
    function addBotPrefix() {
      const inputEl = document.getElementById('new_prefix_input');
      if (!inputEl) return;
      const prefixVal = inputEl.value.trim();
      if (!prefixVal) return;
      
      if (prefixVal.length > 10) {
        showToast("Prefix must be 10 characters or less.", "error");
        return;
      }
      if (currentPrefixes.includes(prefixVal)) {
        showToast("Prefix already added.", "error");
        return;
      }
      currentPrefixes.push(prefixVal);
      renderPrefixesList();
      inputEl.value = '';
    }

    function removeBotPrefix(prefix) {
      currentPrefixes = currentPrefixes.filter(p => p !== prefix);
      renderPrefixesList();
    }

    function renderPrefixesList() {
      const container = document.getElementById('bot_prefixes_list');
      const hiddenInput = document.getElementById('prefix');
      if (!container || !hiddenInput) return;
      
      const val = hiddenInput.value;
      if (val && currentPrefixes.length === 0) {
        currentPrefixes = val.split(',').map(s => s.trim()).filter(Boolean);
      }
      
      hiddenInput.value = currentPrefixes.join(', ');
      container.innerHTML = '';
      
      currentPrefixes.forEach(prefix => {
        const badge = document.createElement('span');
        badge.className = 'badge';
        badge.style.background = 'rgba(255, 255, 255, 0.1)';
        badge.style.color = '#fff';
        badge.style.padding = '5px 10px';
        badge.style.borderRadius = '4px';
        badge.style.fontSize = '0.8rem';
        badge.style.display = 'inline-flex';
        badge.style.alignItems = 'center';
        badge.style.gap = '8px';
        badge.innerHTML = `
          <span><code>${prefix}</code></span>
          <span onclick="removeBotPrefix('${prefix}')" style="cursor:pointer; color:#ef4444; font-weight:bold; font-size:0.9rem;">&times;</span>
        `;
        container.appendChild(badge);
      });
    }

    // Admin roles list builders
    function addAdminRole() {
      const selectEl = document.getElementById('admin_roles_select');
      if (!selectEl) return;
      const roleId = selectEl.value;
      if (!roleId) return;
      
      const roleName = selectEl.options[selectEl.selectedIndex].text;
      if (currentAdminRoles.includes(roleId)) {
        showToast("Role already added.", "error");
        return;
      }
      currentAdminRoles.push(roleId);
      renderAdminRolesList();
      selectEl.value = '';
    }

    function removeAdminRole(roleId) {
      currentAdminRoles = currentAdminRoles.filter(id => id !== roleId);
      renderAdminRolesList();
    }

    function renderAdminRolesList() {
      const container = document.getElementById('admin_roles_list');
      const hiddenInput = document.getElementById('admin_roles');
      if (!container || !hiddenInput) return;
      
      const val = hiddenInput.value;
      if (val && currentAdminRoles.length === 0) {
        try {
          currentAdminRoles = typeof val === 'string' ? JSON.parse(val) : val;
        } catch(e) {
          currentAdminRoles = val.split(',').map(s => s.trim()).filter(Boolean);
        }
      }
      if (!Array.isArray(currentAdminRoles)) {
        currentAdminRoles = [];
      }
      
      hiddenInput.value = JSON.stringify(currentAdminRoles);
      container.innerHTML = '';
      
      currentAdminRoles.forEach(roleId => {
        let roleName = roleId;
        if (activeLayoutData && activeLayoutData.roles) {
          const r = activeLayoutData.roles.find(x => x.id === roleId);
          if (r) roleName = r.name;
        }
        
        const badge = document.createElement('span');
        badge.className = 'badge';
        badge.style.background = 'rgba(10, 255, 228, 0.15)';
        badge.style.color = 'var(--c2)';
        badge.style.padding = '5px 10px';
        badge.style.borderRadius = '4px';
        badge.style.fontSize = '0.8rem';
        badge.style.display = 'inline-flex';
        badge.style.alignItems = 'center';
        badge.style.gap = '8px';
        badge.innerHTML = `
          <span>${roleName}</span>
          <span onclick="removeAdminRole('${roleId}')" style="cursor:pointer; color:#ef4444; font-weight:bold; font-size:0.9rem;">&times;</span>
        `;
        container.appendChild(badge);
      });
    }

    // Mod roles list builders
    function addModRole() {
      const selectEl = document.getElementById('mod_roles_select');
      if (!selectEl) return;
      const roleId = selectEl.value;
      if (!roleId) return;
      
      const roleName = selectEl.options[selectEl.selectedIndex].text;
      if (currentModRoles.includes(roleId)) {
        showToast("Role already added.", "error");
        return;
      }
      currentModRoles.push(roleId);
      renderModRolesList();
      selectEl.value = '';
    }

    function removeModRole(roleId) {
      currentModRoles = currentModRoles.filter(id => id !== roleId);
      renderModRolesList();
    }

    function renderModRolesList() {
      const container = document.getElementById('mod_roles_list');
      const hiddenInput = document.getElementById('mod_roles');
      if (!container || !hiddenInput) return;
      
      const val = hiddenInput.value;
      if (val && currentModRoles.length === 0) {
        try {
          currentModRoles = typeof val === 'string' ? JSON.parse(val) : val;
        } catch(e) {
          currentModRoles = val.split(',').map(s => s.trim()).filter(Boolean);
        }
      }
      if (!Array.isArray(currentModRoles)) {
        currentModRoles = [];
      }
      
      hiddenInput.value = JSON.stringify(currentModRoles);
      container.innerHTML = '';
      
      currentModRoles.forEach(roleId => {
        let roleName = roleId;
        if (activeLayoutData && activeLayoutData.roles) {
          const r = activeLayoutData.roles.find(x => x.id === roleId);
          if (r) roleName = r.name;
        }
        
        const badge = document.createElement('span');
        badge.className = 'badge';
        badge.style.background = 'rgba(10, 255, 228, 0.15)';
        badge.style.color = 'var(--c2)';
        badge.style.padding = '5px 10px';
        badge.style.borderRadius = '4px';
        badge.style.fontSize = '0.8rem';
        badge.style.display = 'inline-flex';
        badge.style.alignItems = 'center';
        badge.style.gap = '8px';
        badge.innerHTML = `
          <span>${roleName}</span>
          <span onclick="removeModRole('${roleId}')" style="cursor:pointer; color:#ef4444; font-weight:bold; font-size:0.9rem;">&times;</span>
        `;
        container.appendChild(badge);
      });
    }

    // Color picker synchronizers
    function syncBotEmbedColorPicker(val) {
      const hexEl = document.getElementById('embed_color');
      if (hexEl) hexEl.value = val;
    }

    function syncBotEmbedColorHex(val) {
      if (/^#[0-9A-F]{6}$/i.test(val)) {
        const pickerEl = document.getElementById('bot_embed_color_picker');
        if (pickerEl) pickerEl.value = val;
      }
    }

// ── MODERATION DROPDOWNS & AUTOMOD CREATOR STUDIO ───────────────────────
    let currentAutomodRules = [];

    function populateModerationDropdowns(roles) {
      const muteRoleSelect = document.getElementById('mod_mute_role');
      if (muteRoleSelect) {
        const oldVal = muteRoleSelect.value;
        muteRoleSelect.innerHTML = '<option value="">-- Select Mute Role --</option>';
        roles.forEach(role => {
          const opt = document.createElement('option');
          opt.value = role.id;
          opt.innerText = role.name;
          muteRoleSelect.appendChild(opt);
        });
        if (oldVal) muteRoleSelect.value = oldVal;
      }

      const logChannelSelect = document.getElementById('mod_log_channel');
      if (logChannelSelect) {
        const oldVal = logChannelSelect.value;
        logChannelSelect.innerHTML = '<option value="">-- Select Log Channel --</option>';
        const textChans = getTextChannels();
        textChans.forEach(chan => {
          const opt = document.createElement('option');
          opt.value = chan.id;
          opt.innerText = `# ${chan.name}`;
          logChannelSelect.appendChild(opt);
        });
        if (oldVal) logChannelSelect.value = oldVal;
      }
    }

    async function populateMusicDropdowns(roles) {
      console.log("[Kaizer] populateMusicDropdowns called with roles:", roles);
      const djRoleSelect = document.getElementById('music_dj_role');
      const musicChannelSelect = document.getElementById('music_channel');
      const voiceChannelSelect = document.getElementById('music_voice_channel');

      if (!djRoleSelect && !musicChannelSelect && !voiceChannelSelect) return;

      let finalRoles = roles || (activeLayoutData ? activeLayoutData.roles : null) || [];
      let textChans = getTextChannels();
      let voiceChans = getVoiceChannels();

      if (finalRoles.length === 0 || textChans.length === 0 || voiceChans.length === 0) {
        console.log("[Kaizer] Music dropdowns: data is empty, attempting to fetch roles/channels directly...");
        try {
          const [rRes, cRes] = await Promise.all([
            fetch(`/api/guild/${guildId}/roles`),
            fetch(`/api/guild/${guildId}/channels`)
          ]);
          const freshRoles = rRes.ok ? await rRes.json() : [];
          const freshChannels = cRes.ok ? await cRes.json() : [];

          if (finalRoles.length === 0 && freshRoles.length > 0) {
            finalRoles = freshRoles.filter(r => r.name !== '@everyone');
          }
          if (textChans.length === 0 && freshChannels.length > 0) {
            textChans = freshChannels.filter(c => c.type === 'text' || (c.type || '').toLowerCase().includes('text'));
          }
          if (voiceChans.length === 0 && freshChannels.length > 0) {
            voiceChans = freshChannels.filter(c => c.type === 'voice' || (c.type || '').toLowerCase().includes('voice'));
          }
        } catch (e) {
          console.error("[Kaizer] Failed to self-heal music dropdowns:", e);
        }
      }

      if (djRoleSelect) {
        const oldVal = djRoleSelect.value;
        djRoleSelect.innerHTML = '<option value="">-- Select DJ Role --</option>';
        finalRoles.forEach(role => {
          if (role && role.id) {
            const opt = document.createElement('option');
            opt.value = role.id;
            opt.innerText = role.name || role.id;
            djRoleSelect.appendChild(opt);
          }
        });
        if (oldVal) djRoleSelect.value = oldVal;
      }

      if (musicChannelSelect) {
        const oldVal = musicChannelSelect.value;
        musicChannelSelect.innerHTML = '<option value="">-- Select Music Text Channel (Any) --</option>';
        textChans.forEach(chan => {
          if (chan && chan.id) {
            const opt = document.createElement('option');
            opt.value = chan.id;
            opt.innerText = `# ${chan.name || chan.id}`;
            musicChannelSelect.appendChild(opt);
          }
        });
        if (oldVal) musicChannelSelect.value = oldVal;
      }

      if (voiceChannelSelect) {
        const oldVal = voiceChannelSelect.value;
        voiceChannelSelect.innerHTML = '<option value="">-- Select Music Voice Channel (Any) --</option>';
        voiceChans.forEach(chan => {
          if (chan && chan.id) {
            const opt = document.createElement('option');
            opt.value = chan.id;
            opt.innerText = `🔊 ${chan.name || chan.id}`;
            voiceChannelSelect.appendChild(opt);
          }
        });
        if (oldVal) voiceChannelSelect.value = oldVal;
      }
      console.log("[Kaizer] Music dropdowns populated successfully.");
    }

    function getVoiceChannels() {
      const list = [];
      if (activeLayoutData && activeLayoutData.categories) {
        activeLayoutData.categories.forEach(cat => {
          if (cat && Array.isArray(cat.channels)) {
            cat.channels.forEach(chan => {
              if (chan && (chan.type === 'voice' || (chan.type || '').toLowerCase().includes('voice'))) {
                list.push(chan);
              }
            });
          }
        });
      }
      return list;
    }

    async function createDJRole() {
      const btn = document.getElementById('btn-create-dj-role');
      if (!btn) return;
      const originalText = btn.innerHTML;
      btn.innerHTML = '<span>Creating...</span>';
      btn.disabled = true;

      try {
        const res = await fetch(`/api/guild/${guildId}/server-action`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ action: 'create_role', role_name: 'DJ', role_color: '#3498bb' })
        });
        const data = await res.json().catch(() => ({}));
        if (res.ok && data.success && data.role) {
          showToast(`DJ role "${data.role.name}" created and configured in Discord!`, 'success');

          if (activeLayoutData) {
            if (!activeLayoutData.roles) activeLayoutData.roles = [];
            if (!activeLayoutData.roles.some(r => r.id === data.role.id)) {
              activeLayoutData.roles.push(data.role);
            }
          }

          populateMusicDropdowns(activeLayoutData.roles);
          const djRoleSelect = document.getElementById('music_dj_role');
          if (djRoleSelect) djRoleSelect.value = data.role.id;
        } else {
          showToast(data.error || 'Failed to create DJ role.', 'error');
        }
      } catch (e) {
        showToast('Network error occurred.', 'error');
      } finally {
        btn.innerHTML = originalText;
        btn.disabled = false;
      }
    }

    async function createMuteRole() {
      const btn = document.getElementById('btn-create-mute-role');
      const originalText = btn.innerHTML;
      btn.innerHTML = '<span>Creating...</span>';
      btn.disabled = true;

      try {
        const res = await fetch(`/api/guild/${guildId}/server-action`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ action: 'create_mute_role' })
        });
        const data = await res.json().catch(() => ({}));
        if (res.ok && data.success && data.role) {
          showToast(`Mute role "${data.role.name}" created and configured in Discord!`, 'success');

          if (activeLayoutData) {
            if (!activeLayoutData.roles) activeLayoutData.roles = [];
            if (!activeLayoutData.roles.some(r => r.id === data.role.id)) {
              activeLayoutData.roles.push(data.role);
            }
          }

          populateModerationDropdowns(activeLayoutData.roles);
          const muteRoleSelect = document.getElementById('mod_mute_role');
          if (muteRoleSelect) muteRoleSelect.value = data.role.id;
        } else {
          showToast(data.error || 'Failed to create mute role.', 'error');
        }
      } catch (e) {
        showToast('Network error occurred.', 'error');
      } finally {
        btn.innerHTML = originalText;
        btn.disabled = false;
      }
    }

    async function createModLogChannel() {
      const btn = document.getElementById('btn-create-mod-log-channel');
      const originalText = btn.innerHTML;
      btn.innerHTML = '<span>Creating...</span>';
      btn.disabled = true;

      try {
        const res = await fetch(`/api/guild/${guildId}/server-action`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ action: 'create_mod_log_channel' })
        });
        const data = await res.json().catch(() => ({}));
        if (res.ok && data.success && data.channel) {
          showToast(`Log channel #${data.channel.name} created successfully!`, 'success');

          if (activeLayoutData) {
            let cat = activeLayoutData.categories.find(c => c.name.toLowerCase().includes('information') || c.name.toLowerCase().includes('welcome') || c.name.toLowerCase().includes('chat'));
            if (!cat && activeLayoutData.categories.length > 0) {
              cat = activeLayoutData.categories[0];
            }
            if (cat) {
              cat.channels.push({ id: data.channel.id, name: data.channel.name, type: 'text' });
            }
          }

          populateModerationDropdowns(activeLayoutData.roles);
          const logChannelSelect = document.getElementById('mod_log_channel');
          if (logChannelSelect) logChannelSelect.value = data.channel.id;
        } else {
          showToast(data.error || 'Failed to create log channel.', 'error');
        }
      } catch (e) {
        showToast('Network error occurred.', 'error');
      } finally {
        btn.innerHTML = originalText;
        btn.disabled = false;
      }
    }

    function addAutomodRule() {
      const trigger = document.getElementById('studio_trigger').value;
      const count = parseInt(document.getElementById('studio_count').value);
      const seconds = parseInt(document.getElementById('studio_seconds').value);
      const action = document.getElementById('studio_action').value;

      if (isNaN(count) || count <= 0 || isNaN(seconds) || seconds <= 0) {
        showToast('Please enter valid positive numbers for limit and seconds.', 'error');
        return;
      }

      const newRule = {
        id: 'rule_' + Date.now() + '_' + Math.floor(Math.random() * 1000),
        trigger: trigger,
        count: count,
        seconds: seconds,
        action: action
      };

      currentAutomodRules.push(newRule);
      document.getElementById('automod_rules').value = JSON.stringify(currentAutomodRules);
      renderAutomodRulesList();
      showToast('Rule added! Remember to save settings.', 'success');
    }

    function removeAutomodRule(ruleId) {
      currentAutomodRules = currentAutomodRules.filter(r => r.id !== ruleId);
      document.getElementById('automod_rules').value = JSON.stringify(currentAutomodRules);
      renderAutomodRulesList();
      showToast('Rule removed! Remember to save settings.', 'success');
    }

    function renderAutomodRulesList() {
      const container = document.getElementById('automod-rules-container');
      if (!container) return;
      container.innerHTML = '';

      if (currentAutomodRules.length === 0) {
        container.innerHTML = '<div style="color: var(--text-muted); font-size: 0.9rem; font-style: italic; padding: 10px 0;">No custom rules built yet.</div>';
        return;
      }

      currentAutomodRules.forEach(rule => {
        let triggerName = 'Spamming Messages';
        if (rule.trigger === 'spam_attachments') triggerName = 'Spamming Images/Videos/Files';
        if (rule.trigger === 'spam_mentions') triggerName = 'Spamming Mentions/Pings';

        let actionName = 'Mute permanently';
        if (rule.action === 'warn') actionName = 'Delete & Warn';
        if (rule.action === 'kick') actionName = 'Kick Member';
        if (rule.action === 'ban') actionName = 'Ban Member';

        const card = document.createElement('div');
        card.style.display = 'flex';
        card.style.justifyContent = 'space-between';
        card.style.alignItems = 'center';
        card.style.background = 'rgba(255, 255, 255, 0.02)';
        card.style.border = '1px solid rgba(255, 255, 255, 0.05)';
        card.style.padding = '10px 15px';
        card.style.marginBottom = '8px';
        card.style.borderRadius = '4px';
        card.style.borderLeft = `3px solid var(--c1)`;

        card.innerHTML = `
          <div>
            <span style="font-weight: bold; color: var(--c1); font-family: monospace;">${triggerName}</span>
            <span style="color: var(--text-muted); margin: 0 8px;">(${rule.count} in ${rule.seconds}s)</span>
            <span style="color: var(--text-muted); margin: 0 8px;">➜</span>
            <span style="font-size: 0.85rem; font-family: monospace; font-weight: bold; color: #ef4444;">
              [Action: ${actionName}]
            </span>
          </div>
          <button type="button" class="btn btn-secondary" style="padding: 6px 12px; font-size: 10px; border-color: var(--c1) !important; color: var(--c1) !important; line-height: 1;" onclick="removeAutomodRule('${rule.id}')">Remove</button>
        `;
        container.appendChild(card);
      });
    }

    function getTextChannels() {
      const list = [];
      if (activeLayoutData && activeLayoutData.categories) {
        activeLayoutData.categories.forEach(cat => {
          if (cat && Array.isArray(cat.channels)) {
            cat.channels.forEach(chan => {
              if (chan && (chan.type === 'text' || (chan.type || '').toLowerCase().includes('text'))) {
                list.push(chan);
              }
            });
          }
        });
      }
      return list;
    }

    // Stats settings helper functions
    function populateStatsDropdowns() {
      const voiceSelect = document.getElementById('stat_voice_channel');
      if (!voiceSelect) return;

      const oldVoiceVal = voiceSelect.value;

      voiceSelect.innerHTML = '<option value="new">-- Create New Voice Channel --</option>';

      const voiceChans = getVoiceChannels();
      voiceChans.forEach(chan => {
        const opt = document.createElement('option');
        opt.value = chan.id;
        opt.innerText = `☊ ${chan.name}`;
        voiceSelect.appendChild(opt);
      });

      if (oldVoiceVal) voiceSelect.value = oldVoiceVal;
    }

    function insertStatPlaceholder(placeholder) {
      const formatInput = document.getElementById('stat_format');
      if (formatInput) {
        const start = formatInput.selectionStart;
        const end = formatInput.selectionEnd;
        const text = formatInput.value;
        const before = text.substring(0, start);
        const after = text.substring(end, text.length);
        formatInput.value = before + placeholder + after;
        formatInput.focus();
        formatInput.selectionStart = formatInput.selectionEnd = start + placeholder.length;
      }
    }

    function renderActiveStatChannels(settings) {
      const container = document.getElementById('stats-channels-list');
      if (!container) return;

      const types = [
        { key: 'total', label: 'Total Members', color: 'var(--accent-cyan)' },
        { key: 'online', label: 'Online Members', color: '#10b981' },
        { key: 'offline', label: 'Offline Members', color: '#6b7280' },
        { key: 'invc', label: 'In Voice (VC)', color: '#a855f7' }
      ];

      let configured = [];
      types.forEach(t => {
        const chanId = settings[`counter_${t.key}_chan_id`];
        const fmt = settings[`counter_${t.key}_fmt`];
        if (chanId) {
          configured.push({
            type: t.key,
            label: t.label,
            color: t.color,
            chanId: chanId,
            format: fmt || `${t.label}: {value}`
          });
        }
      });

      if (configured.length === 0) {
        container.innerHTML = '<div style="color:var(--text-muted); font-style:italic;">No stat channels configured yet.</div>';
        return;
      }

      function findChannelName(id) {
        if (!activeLayoutData || !activeLayoutData.categories) return id;
        for (let cat of activeLayoutData.categories) {
          if (cat.channels) {
            for (let chan of cat.channels) {
              if (chan.id === id) return chan.name;
            }
          }
        }
        return id;
      }

      let html = '<div style="display:flex; flex-direction:column; gap:12px; margin-bottom:15px;">';
      configured.forEach(c => {
        const chanName = findChannelName(c.chanId);
        html += `
          <div style="display:flex; justify-content:space-between; align-items:center; background:rgba(255,255,255,0.03); border:1px solid rgba(255,255,255,0.06); padding:12px; border-radius:8px;">
            <div style="display:flex; align-items:center; gap:10px;">
              <span style="display:inline-block; width:8px; height:8px; border-radius:50%; background:${c.color};"></span>
              <div>
                <div style="font-weight:bold; color:white;">${c.label}</div>
                <div style="font-size:0.8rem; color:var(--text-muted);">
                  Channel: <code style="color:var(--accent-cyan); font-family:monospace;">☊ ${chanName}</code> | Format: <code style="color:var(--accent-cyan); font-family:monospace;">${c.format}</code>
                </div>
              </div>
            </div>
            <button class="btn" onclick="removeStatChannel('${c.type}')" style="background:rgba(239, 68, 68, 0.15); border:1px solid rgba(239, 68, 68, 0.3); color:#f87171; padding:5px 10px; border-radius:4px; font-size:0.8rem; cursor:pointer;">
              Remove
            </button>
          </div>
        `;
      });
      html += '</div>';
      container.innerHTML = html;
    }

    async function removeStatChannel(type) {
      if (!confirm(`Are you sure you want to remove the ${type} stat channel configuration?`)) return;
      try {
        showToast("Removing stat channel...", "info");
        const res = await fetch(`/api/guild/${guildId}/server-action`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ action: 'stats_remove', stat_type: type })
        });
        const data = await res.json();
        if (data.success) {
          showToast("Stat channel removed successfully!", "success");
          await fetchServerLayout();
        } else {
          showToast(data.error || "Failed to remove stat channel.", "error");
        }
      } catch (err) {
        console.error(err);
        showToast("Error removing stat channel.", "error");
      }
    }

    async function handleStatsAdd(event) {
      event.preventDefault();
      const form = event.target;
      const submitBtn = form.querySelector("button[type='submit']");
      const originalText = submitBtn.innerHTML;
      submitBtn.innerHTML = "<span>Creating...</span>";
      submitBtn.disabled = true;

      const stat_type = document.getElementById('stat_type').value;
      const stat_format = document.getElementById('stat_format').value;
      const voice_channel_id = document.getElementById('stat_voice_channel').value;

      try {
        const res = await fetch(`/api/guild/${guildId}/server-action`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            action: 'stats_add',
            stat_type,
            stat_format,
            voice_channel_id
          })
        });
        const data = await res.json();
        if (data.success) {
          showToast("Stat channel configured successfully!", "success");
          await fetchServerLayout();
        } else {
          showToast(data.error || "Failed to configure stat channel.", "error");
        }
      } catch (err) {
        console.error(err);
        showToast("Error configuring stat channel.", "error");
      } finally {
        submitBtn.innerHTML = originalText;
        submitBtn.disabled = false;
      }
    }

    async function handleStatsRefresh(event) {
      event.preventDefault();
      const btn = event.target;
      const originalText = btn.innerHTML;
      btn.innerHTML = "<span>Refreshing...</span>";
      btn.disabled = true;

      try {
        const res = await fetch(`/api/guild/${guildId}/server-action`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ action: 'stats_refresh_all' })
        });
        const data = await res.json();
        if (data.success) {
          showToast(data.message || "Stats refresh triggered!", "success");
          await fetchServerLayout();
        } else {
          showToast(data.error || "Failed to refresh stats.", "error");
        }
      } catch (err) {
        console.error(err);
        showToast("Error refreshing stats.", "error");
      } finally {
        btn.innerHTML = originalText;
        btn.disabled = false;
      }
    }

    // ── DATA SYNC LOADERS ───────────────────────────────────────────────────
    async function loadGuildSettings() {
      try {
        const res = await fetch(`/api/guild/${guildId}/settings`);
        if (!res.ok) return;
        const data = await res.json();
        
        // Populate standard settings fields (e.g. anti-nuke switches)
        Object.keys(data).forEach(key => {
          const el = document.getElementById(key);
          if (!el) return;
          if (el.type === 'checkbox') {
            el.checked = !!data[key];
            el.dispatchEvent(new Event('change'));
          } else {
            el.value = (typeof data[key] === 'object') ? JSON.stringify(data[key]) : (data[key] || '');
          }
        });

        // Render active live stats channels list
        renderActiveStatChannels(data);

        // Special parsing for welcome and goodbye messages
        parseWelcomeMessageOnLoad(data.welcome_message);
        parseGoodbyeMessageOnLoad(data.goodbye_message);

        // Explicitly initialize parent container toggles
        toggleWelcomeFields();
        toggleGoodbyeFields();

        // Parse and render automod_rules
        if (data.automod_rules) {
          try {
            currentAutomodRules = typeof data.automod_rules === 'string' ? JSON.parse(data.automod_rules) : data.automod_rules;
            if (!Array.isArray(currentAutomodRules)) {
              currentAutomodRules = Object.values(currentAutomodRules);
            }
          } catch (e) {
            console.error("Failed to parse automod_rules:", e);
            currentAutomodRules = [];
          }
        } else {
          currentAutomodRules = [];
        }
        document.getElementById('automod_rules').value = JSON.stringify(currentAutomodRules);
        renderAutomodRulesList();

        // Render leveling advanced lists
        renderLevelRolesList();
        renderLevelPermissionsList();

        // Render bot settings dynamic inputs
        currentPrefixes = [];
        renderPrefixesList();
        
        currentAdminRoles = [];
        renderAdminRolesList();
        
        currentModRoles = [];
        renderModRolesList();
        
        // Sync color picker
        const colorVal = data.embed_color || '#0affe4';
        const pickerEl = document.getElementById('bot_embed_color_picker');
        if (pickerEl) pickerEl.value = colorVal;
      } catch (e) {
        console.error("Failed to load guild settings:", e);
      }
    }

    function parseWelcomeMessageOnLoad(val) {
      try {
        const parsed = val ? JSON.parse(val) : null;
        if (parsed && typeof parsed === 'object') {
          // If it is the new rich configuration schema
          if (parsed.message_type) {
            document.getElementById('welcome_embed_enabled').checked = (parsed.message_type === 'embed');
            document.getElementById('welcome_message').value = parsed.text || '';
            
            if (parsed.embed) {
              document.getElementById('welcome_embed_title').value = parsed.embed.title || '';
              document.getElementById('welcome_embed_color_hex').value = parsed.embed.color || '#0affe4';
              document.getElementById('welcome_embed_color').value = parsed.embed.color || '#0affe4';
              document.getElementById('welcome_embed_desc').value = parsed.embed.description || '';
              document.getElementById('welcome_embed_thumbnail').value = parsed.embed.thumbnail || '';
              document.getElementById('welcome_embed_image').value = parsed.embed.image || '';
              document.getElementById('welcome_embed_footer').value = parsed.embed.footer || '';
              document.getElementById('welcome_embed_footer_icon').value = parsed.embed.footer_icon || '';
            }

            // Image settings
            document.getElementById('welcome_image_enabled').checked = !!parsed.image_enabled;
            document.getElementById('welcome_image_style').value = parsed.image_style || 'plain_gradient';
            document.getElementById('welcome_image_color').value = parsed.image_color || 'cyan_neon';
            document.getElementById('welcome_custom_bg_url').value = parsed.custom_bg_url || '';
            
            if (parsed.image_elements) {
              document.getElementById('welcome_image_show_avatar').checked = (parsed.image_elements.avatar !== false);
              document.getElementById('welcome_image_show_username').checked = (parsed.image_elements.username !== false);
              document.getElementById('welcome_image_show_server').checked = (parsed.image_elements.server_name !== false);
              document.getElementById('welcome_image_show_count').checked = (parsed.image_elements.member_count !== false);
              document.getElementById('welcome_image_custom_text').value = parsed.image_elements.custom_text || '';
            }

            // DM settings
            document.getElementById('welcome_dm_enabled').checked = !!parsed.dm_enabled;
            document.getElementById('welcome_dm_embed_enabled').checked = (parsed.dm_type === 'embed');
            document.getElementById('welcome_dm_text').value = parsed.dm_text || '';
            
            if (parsed.dm_embed) {
              document.getElementById('welcome_dm_embed_title').value = parsed.dm_embed.title || '';
              document.getElementById('welcome_dm_embed_color_hex').value = parsed.dm_embed.color || '#0affe4';
              document.getElementById('welcome_dm_embed_color').value = parsed.dm_embed.color || '#0affe4';
              document.getElementById('welcome_dm_embed_desc').value = parsed.dm_embed.description || '';
              document.getElementById('welcome_dm_embed_thumbnail').value = parsed.dm_embed.thumbnail || '';
              document.getElementById('welcome_dm_embed_image').value = parsed.dm_embed.image || '';
              document.getElementById('welcome_dm_embed_footer').value = parsed.dm_embed.footer || '';
              document.getElementById('welcome_dm_embed_footer_icon').value = parsed.dm_embed.footer_icon || '';
            }

            // Activate grids & visual card preview
            syncActivePresetHighlight('welcome', parsed.image_style, parsed.image_color);
            toggleWelcomeEmbedEditor();
            toggleWelcomeImageFields();
            toggleWelcomeDMFields();
            toggleWelcomeDMEmbedEditor();
            updateWelcomeAlertPreview();
            updateWelcomeDMPreview();
            return;
          }
          // If it is the old embed schema
          else if (parsed.embed) {
            document.getElementById('welcome_embed_enabled').checked = true;
            document.getElementById('welcome_embed_title').value = parsed.title || '';
            document.getElementById('welcome_embed_color_hex').value = parsed.color || '#0affe4';
            document.getElementById('welcome_embed_color').value = parsed.color || '#0affe4';
            document.getElementById('welcome_embed_desc').value = parsed.description || '';
            document.getElementById('welcome_embed_thumbnail').value = parsed.thumbnail || '';
            document.getElementById('welcome_embed_image').value = parsed.image || '';
            document.getElementById('welcome_embed_footer').value = parsed.footer || '';
            document.getElementById('welcome_embed_footer_icon').value = parsed.footer_icon || '';
            
            toggleWelcomeEmbedEditor();
            toggleWelcomeImageFields();
            toggleWelcomeDMFields();
            toggleWelcomeDMEmbedEditor();
            updateWelcomeAlertPreview();
            updateWelcomeDMPreview();
            return;
          }
        }
      } catch (_) {}
      
      // Fallback: plain text
      document.getElementById('welcome_embed_enabled').checked = false;
      document.getElementById('welcome_message').value = val || 'Welcome {user} to {server}!';
      toggleWelcomeEmbedEditor();
      toggleWelcomeImageFields();
      toggleWelcomeDMFields();
      toggleWelcomeDMEmbedEditor();
      updateWelcomeAlertPreview();
      updateWelcomeDMPreview();
    }

    function parseGoodbyeMessageOnLoad(val) {
      try {
        const parsed = val ? JSON.parse(val) : null;
        if (parsed && typeof parsed === 'object') {
          // If it is the new rich configuration schema
          if (parsed.message_type) {
            document.getElementById('goodbye_embed_enabled').checked = (parsed.message_type === 'embed');
            document.getElementById('goodbye_message').value = parsed.text || '';
            
            if (parsed.embed) {
              document.getElementById('goodbye_embed_title').value = parsed.embed.title || '';
              document.getElementById('goodbye_embed_color_hex').value = parsed.embed.color || '#ef4444';
              document.getElementById('goodbye_embed_color').value = parsed.embed.color || '#ef4444';
              document.getElementById('goodbye_embed_desc').value = parsed.embed.description || '';
              document.getElementById('goodbye_embed_thumbnail').value = parsed.embed.thumbnail || '';
              document.getElementById('goodbye_embed_image').value = parsed.embed.image || '';
              document.getElementById('goodbye_embed_footer').value = parsed.embed.footer || '';
              document.getElementById('goodbye_embed_footer_icon').value = parsed.embed.footer_icon || '';
            }

            // Image settings
            document.getElementById('goodbye_image_enabled').checked = !!parsed.image_enabled;
            document.getElementById('goodbye_image_style').value = parsed.image_style || 'plain_gradient';
            document.getElementById('goodbye_image_color').value = parsed.image_color || 'cyan_neon';
            document.getElementById('goodbye_custom_bg_url').value = parsed.custom_bg_url || '';
            
            if (parsed.image_elements) {
              document.getElementById('goodbye_image_show_avatar').checked = (parsed.image_elements.avatar !== false);
              document.getElementById('goodbye_image_show_username').checked = (parsed.image_elements.username !== false);
              document.getElementById('goodbye_image_show_server').checked = (parsed.image_elements.server_name !== false);
              document.getElementById('goodbye_image_show_count').checked = (parsed.image_elements.member_count !== false);
              document.getElementById('goodbye_image_custom_text').value = parsed.image_elements.custom_text || '';
            }

            // DM settings
            document.getElementById('goodbye_dm_enabled').checked = !!parsed.dm_enabled;
            document.getElementById('goodbye_dm_embed_enabled').checked = (parsed.dm_type === 'embed');
            document.getElementById('goodbye_dm_text').value = parsed.dm_text || '';
            
            if (parsed.dm_embed) {
              document.getElementById('goodbye_dm_embed_title').value = parsed.dm_embed.title || '';
              document.getElementById('goodbye_dm_embed_color_hex').value = parsed.dm_embed.color || '#ef4444';
              document.getElementById('goodbye_dm_embed_color').value = parsed.dm_embed.color || '#ef4444';
              document.getElementById('goodbye_dm_embed_desc').value = parsed.dm_embed.description || '';
              document.getElementById('goodbye_dm_embed_thumbnail').value = parsed.dm_embed.thumbnail || '';
              document.getElementById('goodbye_dm_embed_image').value = parsed.dm_embed.image || '';
              document.getElementById('goodbye_dm_embed_footer').value = parsed.dm_embed.footer || '';
              document.getElementById('goodbye_dm_embed_footer_icon').value = parsed.dm_embed.footer_icon || '';
            }

            // Activate grids & visual card preview
            syncActivePresetHighlight('goodbye', parsed.image_style, parsed.image_color);
            toggleGoodbyeEmbedEditor();
            toggleGoodbyeImageFields();
            toggleGoodbyeDMFields();
            toggleGoodbyeDMEmbedEditor();
            updateGoodbyeAlertPreview();
            updateGoodbyeDMPreview();
            return;
          }
          // If it is the old embed schema
          else if (parsed.embed) {
            document.getElementById('goodbye_embed_enabled').checked = true;
            document.getElementById('goodbye_embed_title').value = parsed.title || '';
            document.getElementById('goodbye_embed_color_hex').value = parsed.color || '#ef4444';
            document.getElementById('goodbye_embed_color').value = parsed.color || '#ef4444';
            document.getElementById('goodbye_embed_desc').value = parsed.description || '';
            document.getElementById('goodbye_embed_thumbnail').value = parsed.thumbnail || '';
            document.getElementById('goodbye_embed_image').value = parsed.image || '';
            document.getElementById('goodbye_embed_footer').value = parsed.footer || '';
            document.getElementById('goodbye_embed_footer_icon').value = parsed.footer_icon || '';
            
            toggleGoodbyeEmbedEditor();
            toggleGoodbyeImageFields();
            toggleGoodbyeDMFields();
            toggleGoodbyeDMEmbedEditor();
            updateGoodbyeAlertPreview();
            updateGoodbyeDMPreview();
            return;
          }
        }
      } catch (_) {}
      
      // Fallback: plain text
      document.getElementById('goodbye_embed_enabled').checked = false;
      document.getElementById('goodbye_message').value = val || '{user} left the server.';
      toggleGoodbyeEmbedEditor();
      toggleGoodbyeImageFields();
      toggleGoodbyeDMFields();
      toggleGoodbyeDMEmbedEditor();
      updateGoodbyeAlertPreview();
      updateGoodbyeDMPreview();
    }

    function syncActivePresetHighlight(prefix, style, color) {
      const grid = document.getElementById(`${prefix}_presets_grid`);
      if (!grid) return;
      grid.querySelectorAll('.preset-btn').forEach(btn => {
        if (btn.dataset.style === style && btn.dataset.color === color) {
          btn.classList.add('active');
        } else {
          btn.classList.remove('active');
        }
      });
    }

    // ── ECONOMY SHOP MANAGEMENT ─────────────────────────────────────────────
    async function loadShopItems() {
      const container = document.getElementById('shop-items-list');
      if (!container) return;
      container.innerHTML = '<div style="color: var(--text-muted); font-style: italic;">Loading shop items...</div>';
      try {
        const res = await fetch(`/api/guild/${guildId}/shop_items`);
        const items = await res.json();
        if (Array.isArray(items)) {
          renderShopItemsList(items);
        } else {
          container.innerHTML = '<div style="color: #ef4444; font-style: italic;">Failed to load shop items.</div>';
        }
      } catch (err) {
        console.error(err);
        container.innerHTML = '<div style="color: #ef4444; font-style: italic;">Error fetching shop items.</div>';
      }
    }

    function renderShopItemsList(items) {
      const container = document.getElementById('shop-items-list');
      if (!container) return;
      if (!items || items.length === 0) {
        container.innerHTML = '<p style="color: var(--text-muted); font-style: italic; margin: 0;">No shop items created yet.</p>';
        return;
      }
      
      let html = '<div style="display: flex; flex-direction: column; gap: 10px;">';
      items.forEach(item => {
        const emojiStr = item.emoji ? `<span style="margin-right: 5px;">${item.emoji}</span>` : '';
        const descStr = item.description ? `<div style="font-size: 0.85rem; color: var(--text-muted); margin-top: 4px;">${item.description}</div>` : '';
        const roleLabel = item.role_id ? `<span style="background: rgba(10, 255, 228, 0.12); color: var(--c2); border: 1px solid rgba(10, 255, 228, 0.25); padding: 2px 6px; border-radius: 4px; font-size: 0.7rem; margin-left: 8px;">Role linked</span>` : '';
        
        html += `
          <div style="padding: 12px 15px; display: flex; justify-content: space-between; align-items: center; background: rgba(255, 255, 255, 0.02); border-radius: 6px; border: 1px solid rgba(255, 255, 255, 0.06);">
            <div>
              <div style="font-weight: bold; color: #fff; font-size: 0.95rem; display: flex; align-items: center;">
                ${emojiStr}${item.name}
                <span style="color: var(--c2); margin-left: 10px; font-size: 0.85rem;">(${item.price} coins)</span>
                <span style="background: rgba(255, 255, 255, 0.06); color: var(--text-muted); padding: 2px 6px; border-radius: 4px; font-size: 0.7rem; margin-left: 8px; text-transform: uppercase;">${item.type || 'item'}</span>
                ${roleLabel}
              </div>
              ${descStr}
            </div>
            <button class="btn" onclick="deleteShopItem('${item.name}')" style="background: rgba(239, 68, 68, 0.2); border: 1px solid rgba(239, 68, 68, 0.4); color: #f87171; padding: 5px 10px; border-radius: 4px; cursor: pointer; transition: all 0.2s; font-size: 0.8rem;" onmouseover="this.style.background='rgba(239, 68, 68, 0.35)'" onmouseout="this.style.background='rgba(239, 68, 68, 0.2)'">
              Remove
            </button>
          </div>
        `;
      });
      html += '</div>';
      container.innerHTML = html;
    }

    async function deleteShopItem(itemName) {
      if (!confirm(`Are you sure you want to delete the shop item "${itemName}"?`)) return;
      try {
        showToast("Deleting shop item...", "info");
        const res = await fetch(`/api/guild/${guildId}/shop_items/${encodeURIComponent(itemName)}`, {
          method: 'DELETE'
        });
        const data = await res.json();
        if (data.success) {
          showToast(data.message || "Shop item deleted successfully!", "success");
          loadShopItems();
        } else {
          showToast(data.error || "Failed to delete shop item.", "error");
        }
      } catch (err) {
        console.error(err);
        showToast("Error deleting shop item.", "error");
      }
    }

    // Intercept saveSettings to refresh shop list when a new item is added
    if (typeof window.saveSettings === 'function') {
      const originalSaveSettings = window.saveSettings;
      window.saveSettings = async function(event, category) {
        if (category === 'stats_add') {
          await handleStatsAdd(event);
          return;
        }
        if (category === 'stats_refresh') {
          await handleStatsRefresh(event);
          return;
        }
        await originalSaveSettings(event, category);
        if (category === 'economy_shop_add') {
          const nameInput = document.getElementById('shop_item_name');
          if (nameInput) nameInput.value = '';
          loadShopItems();
        }
      };
    } else {
      // In case window.saveSettings isn't defined yet at execution time, hook it dynamically
      const timer = setInterval(() => {
        if (typeof window.saveSettings === 'function') {
          clearInterval(timer);
          const originalSaveSettings = window.saveSettings;
          window.saveSettings = async function(event, category) {
            if (category === 'stats_add') {
              await handleStatsAdd(event);
              return;
            }
            if (category === 'stats_refresh') {
              await handleStatsRefresh(event);
              return;
            }
            await originalSaveSettings(event, category);
            if (category === 'economy_shop_add') {
              const nameInput = document.getElementById('shop_item_name');
              if (nameInput) nameInput.value = '';
              loadShopItems();
            }
          };
        }
      }, 50);
    }

    // Dom Load
    document.addEventListener('DOMContentLoaded', () => { 
      initFontSelectorOptions();
      renderDecoratorPresets();
      loadCommandsForCategory('moderation'); 
      loadActiveTempVCs();
      fetchServerLayout();
      previewFont();
      handleTargetChannelChange();



      // Render preset card selectors
      renderPresetsGrid('welcome');
      renderPresetsGrid('goodbye');

      
      loadShopItems();
      
    });
  