import string

# Define the base alphabet
ALPHABET = "abcdefghijklmnopqrstuvwxyz"

FONT_MAPS = {
    "FN-01": "𝓪𝓫𝓬𝓭𝓮𝓯𝓰𝓱𝓲𝓳𝓴𝓵𝓶𝓷𝓸𝓹𝓺𝓻𝓼𝓽𝓾𝓿𝔀𝔁𝔂𝔃",
    "FN-02": "𝔞𝔟𝔠𝔡𝔢𝔣𝔤𝔥𝔦𝔧𝔨𝔩𝔪𝔫𝔬𝔭𝔮𝔯𝔰𝔱𝔲𝔳𝔴𝔵𝔶 individual characters for fraktur", # I'll fix this
}

def get_font_maps():
    styles = {
        "FN-01": "𝓪𝓫𝓬𝓭𝓮𝓯𝓰𝓱𝓲𝓳𝓴𝓵𝓶𝓷𝓸𝓹𝓺𝓻𝓼𝓽𝓾𝓿𝔀𝔁𝔂𝔃", # Cursive Script
        "FN-02": "𝔞𝔟𝔠𝔡𝔢𝔣𝔤𝔥𝔦𝔧𝔨𝔩𝔪𝔫𝔬𝔭𝔮𝔯𝔰𝔱𝔲𝔳𝔴𝔵𝔶𝔷", # Gothic
        "FN-03": "𝕒𝕓𝕔𝕕𝕖𝕗𝕘𝕙𝕚𝕛𝕜𝕝𝕞𝕟𝕠𝕡𝕢𝕣𝕤𝕥𝕦𝕧𝕨𝕩𝕪𝕫", # Bold Gothic / Blackboard
        "FN-04": "𝐚𝐛𝐜𝐝𝐞𝐟𝐠𝐡𝐢𝐣𝐤𝐥𝐦𝐧𝐨𝐩𝐪𝐫𝐬𝐭𝐮𝐯𝐰𝐱𝐲𝐳", # Math Bold
        "FN-05": "𝑎𝑏𝑐𝑑𝑒𝑓𝑔ℎ𝑖𝑗𝑘𝑙𝑚𝑛𝑜𝑝𝑞𝑟𝑠𝑡𝑢𝑣𝑤𝑥𝑦𝑧", # Math Italic
        "FN-06": "𝒂𝒃𝒄𝒅𝒆𝒇𝒈𝒉𝒊𝒋𝒌𝒍𝒎𝒏𝒐𝒑𝒒𝒓𝒔𝒕𝒖𝒗𝒘𝒙𝒚𝒛", # Bold Italic
        "FN-07": "𝚊𝚋𝚌𝚍𝚎𝚏𝚐𝚑𝚒𝚓𝚔𝚕𝚖𝚗𝚘𝚙𝚚𝚛𝚜𝚝𝚞𝚟𝚠𝚡𝚢𝚣", # Monospace
        "FN-08": "𝗮𝗯𝗰𝗱𝗲𝗳𝗴𝗵𝗶𝗷𝗸𝗹𝗺𝗻𝗼𝗽𝗾𝗿𝘀𝘁𝘂𝘃𝘄𝘅𝘆𝘇", # Sans Bold
        "FN-09": "𝘢𝘣𝘤𝘥𝘦𝘧𝘨𝘩𝘪𝘫𝘬𝘭𝘮𝘯𝘰𝘱𝘲𝘳𝘴𝘵𝘶𝘷𝘸𝘹𝘺𝘻", # Sans Italic
        "FN-10": "𝙖𝙗𝙘𝙙𝙚𝙛𝙜𝙝𝙞𝙟𝙠𝙡𝙢𝙣𝙤𝙥𝙦𝙧𝙨𝙩𝙪𝙫𝙬𝙭𝙮𝙯", # Sans Bold Italic
        "FN-11": "ａｂｃｄｅｆｇｈｉｊｋｌｍｎｏｐｑｒｓｔｕｖｗｘｙｚ", # Fullwidth
        "FN-12": "ᴀʙᴄᴅᴇꜰɢʜɪᴊᴋʟᴍɴᴏᴘQʀꜱᴛᴜᴠᴡxʏᴢ", # Small Caps
        "FN-13": "ᵃᵇᶜᵈᵉᶠᵍʰⁱʲᵏˡᵐⁿᵒᵖᵠʳˢᵗᵘᵛʷˣʸᶻ", # Superscript
        "FN-14": "ⓐⓑⓒⓓⓔⓕⓖⓗⓘⓙⓚⓛⓜⓝⓞⓟⓠⓡⓢⓣⓤⓥⓦⓧⓨⓩ", # Circled
        "FN-15": "🄰🄱🄲🄳🄴🄵🄶🄷🄸🄹🄺🄻🄼🄽🄾🄿🅀🅁🅂🅃🅄🅅🅆🅇🅈🅉", # Squared
        "FN-16": "", # Filled Squares
        "FN-17": "ɐqɔpǝɟƃɥıɾʞlɯuodbɹsʇnʌʍxʎz", # Upside Down
        "FN-18": "dqpqǝɟƃɥᴉɾʞlɯuodbɹsʇnʌʍxʎz", # Mirror (Approximation)
    }
    
    decorations = {
        "FN-19": ("{char}\u0336", ""), # Strikethrough
        "FN-20": ("{char}\u0332", ""), # Underline Deco
        "FN-21": (" {word} ", ""),
        "FN-22": (" {word} ", ""),
        "FN-23": (" {word} ", ""),
        "FN-24": (" {word} ", ""),
        "FN-25": ("◈ {word} ◈", ""),
        "FN-26": ("◇ {word} ◇", ""),
        "FN-27": ("◆ {word} ◆", ""),
        "FN-28": ("⬪ {word} ⬪", ""),
        "FN-29": ("⬡ {word} ⬡", ""),
        "FN-30": ("▲ {word} ▲", ""),
        "FN-31": ("▼ {word} ▼", ""),
        "FN-32": ("» {word} «", ""),
        "FN-33": ("« {word} »", ""),
        "FN-34": ("┇ {word} ‧", ""),
        "FN-35": ("┇ ٫ {word} ‧", ""),
        "FN-36": ("⬪ ٫ {word} ‧", ""),
        "FN-37": ("┇ ٫ {word} | ", ""),
        "FN-38": (" ─ {word} ─ ", ""),
        "FN-39": ("⬪ ₊ {word} ₊ ⬪", ""),
        "FN-40": ("» {word} | ", ""),
        "FN-41": ("» ٫ {word} ‧", ""),
        "FN-42": ("┇ {word} ┇", ""),
        "FN-43": ("┊ {word} ┊", ""),
        "FN-44": ("┋ {word} ┋", ""),
        "FN-45": ("━ {word} ━", ""),
        "FN-46": ("─ {word} ─", ""),
        "FN-47": ("═ {word} ═", ""),
        "FN-48": ("░ {word} ░", ""),
        "FN-49": ("▒ {word} ▒", ""),
        "FN-50": ("▓ {word} ▓", ""),
        "FN-51": ("[EDIT] {word}", ""),
        "FN-52": ("[EDIT] {word}", ""),
        "FN-53": ("[FEATHER] {word}", ""),
        "FN-54": ("[!] {word}", ""),
        "FN-55": ("[PLANET] {word}", ""),
        "FN-56": ("[SETTINGS] {word}", ""),
        "FN-57": ("[SCALE] {word}", ""),
        "FN-58": ("[BATTLE] {word}", ""),
        "FN-59": (" {word} ", ""),
        "FN-60": (" {word} ", ""),
        "FN-61": (" {word}", ""),
        "FN-62": (" {word}", ""),
        "FN-63": (" {word}", ""),
        "FN-64": (" {word}", ""),
        "FN-65": (" {word}", ""),
        "FN-66": (" {word}", ""),
        "FN-67": (" {word}", ""),
        "FN-68": (" {word}", ""),
        "FN-69": ("[PEACE] {word} [PEACE]", ""),
        "FN-70": ("[YIN_YANG] {word} [YIN_YANG]", ""),
        "FN-71": ("[WHEEL] {word} [WHEEL]", ""),
        "FN-72": ("[SUN] {word} [SUN]", ""),
        "FN-73": ("[MOON] {word} [MOON]", ""),
        "FN-74": ("[MOON] {word} [MOON]", ""),
        "FN-75": ("[CLOUD] {word} [CLOUD]", ""),
        "FN-76": ("[COMET] {word} [COMET]", ""),
        "FN-77": (" {word}", ""),
        "FN-78": (" {word}", ""),
        "FN-79": (" {word}", ""),
        "FN-80": (" {word}", ""),
        "FN-81": (" {word}", ""),
        "FN-82": (" {word}", ""),
        "FN-83": (" {word}", ""),
        "FN-84": ("⟨ {word} ⟩", ""),
        "FN-85": ("〔 {word} 〕", ""),
        "FN-86": ("【 {word} 】", ""),
        "FN-87": ("〖 {word} 〗", ""),
        "FN-88": ("𓆩 {word} 𓆪", ""),
        "FN-89": ("𓏲 {word} 𓏲", ""),
        "FN-90": ("𓍢 {word} 𓍢", ""),
        "FN-91": ("𓏴 {word} 𓏴", ""),
        "FN-92": ("𓈀 {word} 𓈀", ""),
        "FN-93": ("𓂋 {word} 𓂋", ""),
        "FN-94": ("𓆩 ٫ {word} ‧ 𓆪", ""),
        "FN-95": ("𓏲 ٫ {word} ‧ 𓏲", ""),
        "FN-96": ("𓍢 ٫ {word} ‧ 𓍢", ""),
        "FN-97": ("𓏴 ٫ {word} ‧ 𓏴", ""),
        "FN-98": ("𓈀 ٫ {word} ‧ 𓈀", ""),
        "FN-99": ("𓂋 ٫ {word} ‧ 𓂋", ""),
        "FN-100": ("» {word} «", ""),
        "FN-101": ("[DANGER] {word} [DANGER]", ""),
        "FN-102": ("[RADIATION] {word} [RADIATION]", ""),
        "FN-103": ("[BIOHAZARD] {word} [BIOHAZARD]", ""),
        "FN-104": ("[PEACE] {word} [PEACE]", ""),
        "FN-105": ("[YIN_YANG] {word} [YIN_YANG]", ""),
    }
    
    return styles, decorations

def apply_font_to_string(text, font_id):
    styles, decorations = get_font_maps()
    text = text.lower()
    
    # Base font substitution
    base_style_id = font_id
    try:
        f_num = int(font_id.split("-")[1])
    except (ValueError, IndexError):
        f_num = 1
        
    if font_id in ["FN-19", "FN-20"]:
        base_style_id = "FN-07"
    elif 21 <= f_num <= 30:
        base_style_id = "FN-01"
    elif 31 <= f_num <= 40:
        base_style_id = "FN-02"
    elif 41 <= f_num <= 50:
        base_style_id = "FN-03"
    elif 51 <= f_num <= 60:
        base_style_id = "FN-04"
    elif 61 <= f_num <= 70:
        base_style_id = "FN-05"
    elif 71 <= f_num <= 80:
        base_style_id = "FN-06"
    elif 81 <= f_num <= 90:
        base_style_id = "FN-07"
    elif 91 <= f_num <= 100:
        base_style_id = "FN-12"
    elif 101 <= f_num <= 105:
        base_style_id = "FN-11"

    mapped_chars = []
    style_str = styles.get(base_style_id)
    
    if style_str:
        for char in text:
            if char in ALPHABET:
                idx = ALPHABET.index(char)
                if idx < len(style_str):
                    mapped_chars.append(style_str[idx])
                else:
                    mapped_chars.append(char)
            else:
                mapped_chars.append(char)
        base_word = "".join(mapped_chars)
    else:
        base_word = text

    # Apply decoration layer
    if font_id in decorations:
        deco_pattern = decorations[font_id][0]
        # if the pattern requires per-character replacement (like strikethrough)
        if "{char}" in deco_pattern:
            decorated = "".join([deco_pattern.format(char=c) if c != ' ' else ' ' for c in base_word])
            return decorated
        else:
            return deco_pattern.format(word=base_word)
            
    return base_word

def clean_styled_string(text):
    styles, _ = get_font_maps()
    reverse_map = {}
    for style_str in styles.values():
        for idx, char in enumerate(style_str):
            if idx < len(ALPHABET):
                if char not in ALPHABET and char not in ALPHABET.upper():
                    reverse_map[char] = ALPHABET[idx]
                
    keep_chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 -_"
    
    cleaned_chars = []
    for char in text:
        if char in reverse_map:
            cleaned_chars.append(reverse_map[char])
        elif char in keep_chars:
            cleaned_chars.append(char)
            
    cleaned_str = "".join(cleaned_chars)
    cleaned_str = cleaned_str.strip(" -_")
    return " ".join(cleaned_str.split())

