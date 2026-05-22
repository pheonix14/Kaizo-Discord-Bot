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
        "FN-16": "🅰🅱🅲🅳🅴🅵🅶🅷🅸🅹🅺🅻🅼🅽🅾🅿🆀🆁🆂🆃🆄🆅🆆🆇🆈🆉", # Filled Squares
        "FN-17": "ɐqɔpǝɟƃɥıɾʞlɯuodbɹsʇnʌʍxʎz", # Upside Down
        "FN-18": "dqpqǝɟƃɥᴉɾʞlɯuodbɹsʇnʌʍxʎz", # Mirror (Approximation)
    }
    
    decorations = {
        "FN-19": ("{char}\u0336", ""), # Strikethrough
        "FN-20": ("{char}\u0332", ""), # Underline Deco
        "FN-21": ("· {word}", "·"), # Cursive + Dots
        "FN-22": ("━ {word} ━", ""), # Gothic + Lines
        "FN-23": ("[ {word} ]", ""), # Bold + Brackets
        "FN-24": ("╰ {word} ╯", ""), # Fullwidth + Corners
        "FN-25": ("✦ {word} ✦", ""), # Small Caps + Sparkle
        "FN-26": ("▸ {word}", ""), # Circled + Arrow
        "FN-27": ("〜 {word} 〜", ""), # Italic + Wave
        "FN-28": ("· {word} ·", ""), # Superscript + Dot
        "FN-29": ("{word}", ""), # Mixed Cursive Bold
        "FN-30": ("{word} ♡", ""), # Cursive + Heart
        "FN-31": ("✧ {word} ✧", ""), # Gothic + Star
        "FN-32": ("{word} ₊˚", ""), # Bold + Sub Dot
        "FN-33": ("｡ {word} ｡", ""), # Fullwidth Soft
        "FN-34": ("━ {word} ━", ""), # Small Caps Bar
        "FN-35": ("·· {word} ··", ""), # Circled Dots
        "FN-36": ("「{word}」", ""), # Mono Corner
        "FN-37": ("꒰ {word} ꒱", ""), # Bold Italic + Curlicue
        "FN-38": ("{word}\u0336 ⌇", ""), # Strikethrough Ghost
        "FN-39": ("⟨ {word}\u0332 ⟩", ""), # Underline + Angle
        "FN-40": ("{word}<3", ""), # Cursive Gothic Mix
    }
    
    return styles, decorations

def apply_font_to_string(text, font_id):
    styles, decorations = get_font_maps()
    text = text.lower()
    
    # Base font substitution
    base_style_id = font_id
    # Some FN mapping combine styles and decorations
    if font_id == "FN-19": base_style_id = "FN-07" # just normal text with strikethrough
    elif font_id == "FN-20": base_style_id = "FN-07"
    elif font_id == "FN-21": base_style_id = "FN-01"
    elif font_id == "FN-22": base_style_id = "FN-02"
    elif font_id == "FN-23": base_style_id = "FN-04"
    elif font_id == "FN-24": base_style_id = "FN-11"
    elif font_id == "FN-25": base_style_id = "FN-12"
    elif font_id == "FN-26": base_style_id = "FN-14"
    elif font_id == "FN-27": base_style_id = "FN-05"
    elif font_id == "FN-28": base_style_id = "FN-13"
    elif font_id == "FN-29": base_style_id = "FN-06"
    elif font_id == "FN-30": base_style_id = "FN-01"
    elif font_id == "FN-31": base_style_id = "FN-02"
    elif font_id == "FN-32": base_style_id = "FN-04"
    elif font_id == "FN-33": base_style_id = "FN-11"
    elif font_id == "FN-34": base_style_id = "FN-12"
    elif font_id == "FN-35": base_style_id = "FN-14"
    elif font_id == "FN-36": base_style_id = "FN-07"
    elif font_id == "FN-37": base_style_id = "FN-06"
    elif font_id == "FN-38": base_style_id = "FN-07"
    elif font_id == "FN-39": base_style_id = "FN-07"
    elif font_id == "FN-40": base_style_id = "FN-02"

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
