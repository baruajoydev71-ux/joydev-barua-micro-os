with open(r'C:\Users\barua\.gemini\antigravity\scratch\micro-os\scripts\build_clean_interactive_os.py', 'r') as f:
    text = f.read()

# Replace click handler section with clean label-based code
old_section = """    # =========================================================================
    # Click Handler: Click at (mouse_x, mouse_y)
    # =========================================================================
    a.label('do_click')
    # Check if close button clicked: x >= 580 and y <= 45 and active_view > 0
    a.emit(b'\\x81\\x3E\\x02\\x1F\\x44\\x02') # cmp word [0x1F02], 580
    a.j_rel8(b'\\x72', 'check_dock_click')
    a.emit(b'\\x83\\x3E\\x04\\x1F\\x2D')      # cmp word [0x1F04], 45
    a.j_rel8(b'\\x77', 'check_dock_click')
    # Clicked close button!
    a.emit(b'\\xC7\\x06\\x00\\x1F\\x00\\x00') # active_view = 0
    a.j_near(b'\\xE9', 'redraw_all')

    a.label('check_dock_click')
    # If y >= 365: Click is on Bottom Dock!
    a.emit(b'\\x81\\x3E\\x04\\x1F\\x6D\\x01') # cmp word [0x1F04], 365
    a.j_rel8(b'\\x72', 'check_icon_click')

    # Dock items:
    a.emit(b'\\x8B\\x1E\\x02\\x1F')          # mov bx, [0x1F02] (x)
    a.emit(b'\\x81\\xFB\\x90\\x01')          # cmp bx, 400
    a.j_rel8(b'\\x72', 'dock_apps_check')

    # Workspace pills:
    a.emit(b'\\x81\\xFB\\xF4\\x01')          # cmp bx, 500
    a.j_rel8(b'\\x77', 'dock_ws2')
    a.emit(b'\\xC7\\x06\\x00\\x1F\\x00\\x00')  # WS1 -> View 0
    a.j_near(b'\\xE9', 'redraw_all')

    a.label('dock_ws2')
    a.emit(b'\\x81\\xFB\\x26\\x02')          # cmp bx, 550
    a.j_rel8(b'\\x77', 'dock_ws3')
    a.emit(b'\\xC7\\x06\\x00\\x1F\\x01\\x00')  # WS2 -> View 1 (Wi-Fi)
    a.j_near(b'\\xE9', 'redraw_all')

    a.label('dock_ws3')
    a.emit(b'\\x81\\xFB\\x58\\x02')          # cmp bx, 600
    a.j_rel8(b'\\x77', 'dock_ws4')
    a.emit(b'\\xC7\\x06\\x00\\x1F\\x02\\x00')  # WS3 -> View 2 (Hardware)
    a.j_near(b'\\xE9', 'redraw_all')

    a.label('dock_ws4')
    a.emit(b'\\xC7\\x06\\x00\\x1F\\x04\\x00')  # WS4 -> View 4 (Terminal)
    a.j_near(b'\\xE9', 'redraw_all')

    a.label('dock_apps_check')
    # Terminal icon around x=86
    a.emit(b'\\x81\\xFB\\x50\\x00\\x72\\x08\\x81\\xFB\\x6A\\x00\\x77\\x08')
    a.emit(b'\\xC7\\x06\\x00\\x1F\\x04\\x00')  # View 4
    a.j_near(b'\\xE9', 'redraw_all')
    # Wi-Fi icon around x=110
    a.emit(b'\\x81\\xFB\\x6A\\x00\\x72\\x08\\x81\\xFB\\x84\\x00\\x77\\x08')
    a.emit(b'\\xC7\\x06\\x00\\x1F\\x01\\x00')  # View 1
    a.j_near(b'\\xE9', 'redraw_all')
    # Monitor icon around x=134
    a.emit(b'\\x81\\xFB\\x84\\x00\\x72\\x08\\x81\\xFB\\x9E\\x00\\x77\\x08')
    a.emit(b'\\xC7\\x06\\x00\\x1F\\x03\\x00')  # View 3
    a.j_near(b'\\xE9', 'redraw_all')
    a.j_near(b'\\xE9', 'event_loop')

    a.label('check_icon_click')
    # Desktop icon clicks:
    # If Col 2, Wi-Fi icon: x in [180..300], y in [130..165] -> View 1 (Wi-Fi)
    a.emit(b'\\x8B\\x1E\\x02\\x1F\\x8B\\x0E\\x04\\x1F') # BX=x, CX=y
    a.emit(b'\\x81\\xFB\\xB4\\x00\\x72\\x15\\x81\\xFB\\x2C\\x01\\x77\\x0F') # x in 180..300
    a.emit(b'\\x81\\xF9\\x82\\x00\\x72\\x09\\x81\\xF9\\xA5\\x00\\x77\\x03') # y in 130..165
    a.emit(b'\\xC7\\x06\\x00\\x1F\\x01\\x00')  # View 1
    a.j_near(b'\\xE9', 'redraw_all')

    # If Col 1, Sys Monitor: x in [14..160], y in [130..165] -> View 3 (Monitor)
    a.emit(b'\\x81\\xFB\\x0E\\x00\\x72\\x15\\x81\\xFB\\xA0\\x00\\x77\\x0F')
    a.emit(b'\\x81\\xF9\\x82\\x00\\x72\\x09\\x81\\xF9\\xA5\\x00\\x77\\x03')
    a.emit(b'\\xC7\\x06\\x00\\x1F\\x03\\x00')  # View 3
    a.j_near(b'\\xE9', 'redraw_all')

    # If Col 1, Hardware: x in [14..160], y in [315..355] -> View 2 (Hardware)
    a.emit(b'\\x81\\xFB\\x0E\\x00\\x72\\x15\\x81\\xFB\\xA0\\x00\\x77\\x0F')
    a.emit(b'\\x81\\xF9\\x3B\\x01\\x72\\x09\\x81\\xF9\\x63\\x01\\x77\\x03')
    a.emit(b'\\xC7\\x06\\x00\\x1F\\x02\\x00')  # View 2
    a.j_near(b'\\xE9', 'redraw_all')

    a.j_near(b'\\xE9', 'event_loop')"""

new_section = """    # =========================================================================
    # Click Handler: Click at (mouse_x, mouse_y)
    # =========================================================================
    a.label('do_click')
    # Check if close button clicked: x >= 580 and y <= 45
    a.emit(b'\\x81\\x3E\\x02\\x1F\\x44\\x02') # cmp word [0x1F02], 580
    a.j_rel8(b'\\x72', 'check_dock_click')
    a.emit(b'\\x83\\x3E\\x04\\x1F\\x2D')      # cmp word [0x1F04], 45
    a.j_rel8(b'\\x77', 'check_dock_click')
    a.emit(b'\\xC7\\x06\\x00\\x1F\\x00\\x00') # active_view = 0
    a.j_near(b'\\xE9', 'redraw_all')

    a.label('check_dock_click')
    # If y >= 365: Click is on Bottom Dock!
    a.emit(b'\\x81\\x3E\\x04\\x1F\\x6D\\x01') # cmp word [0x1F04], 365
    a.j_rel8(b'\\x73', 'is_dock')
    a.j_near(b'\\xE9', 'check_icon_click')
    a.label('is_dock')

    # Dock items:
    a.emit(b'\\x8B\\x1E\\x02\\x1F')          # mov bx, [0x1F02] (x)
    a.emit(b'\\x81\\xFB\\x90\\x01')          # cmp bx, 400
    a.j_rel8(b'\\x72', 'dock_apps_check')

    # Workspace pills:
    a.emit(b'\\x81\\xFB\\xF4\\x01')          # cmp bx, 500
    a.j_rel8(b'\\x77', 'dock_ws2')
    a.emit(b'\\xC7\\x06\\x00\\x1F\\x00\\x00')  # WS1 -> View 0
    a.j_near(b'\\xE9', 'redraw_all')

    a.label('dock_ws2')
    a.emit(b'\\x81\\xFB\\x26\\x02')          # cmp bx, 550
    a.j_rel8(b'\\x77', 'dock_ws3')
    a.emit(b'\\xC7\\x06\\x00\\x1F\\x01\\x00')  # WS2 -> View 1 (Wi-Fi)
    a.j_near(b'\\xE9', 'redraw_all')

    a.label('dock_ws3')
    a.emit(b'\\x81\\xFB\\x58\\x02')          # cmp bx, 600
    a.j_rel8(b'\\x77', 'dock_ws4')
    a.emit(b'\\xC7\\x06\\x00\\x1F\\x02\\x00')  # WS3 -> View 2 (Hardware)
    a.j_near(b'\\xE9', 'redraw_all')

    a.label('dock_ws4')
    a.emit(b'\\xC7\\x06\\x00\\x1F\\x04\\x00')  # WS4 -> View 4 (Terminal)
    a.j_near(b'\\xE9', 'redraw_all')

    a.label('dock_apps_check')
    # Terminal icon around x=86 (80..106)
    a.emit(b'\\x81\\xFB\\x50\\x00')
    a.j_rel8(b'\\x72', 'not_dock_term')
    a.emit(b'\\x81\\xFB\\x6A\\x00')
    a.j_rel8(b'\\x77', 'not_dock_term')
    a.emit(b'\\xC7\\x06\\x00\\x1F\\x04\\x00')  # View 4
    a.j_near(b'\\xE9', 'redraw_all')
    a.label('not_dock_term')

    # Wi-Fi icon around x=110 (106..132)
    a.emit(b'\\x81\\xFB\\x6A\\x00')
    a.j_rel8(b'\\x72', 'not_dock_wifi')
    a.emit(b'\\x81\\xFB\\x84\\x00')
    a.j_rel8(b'\\x77', 'not_dock_wifi')
    a.emit(b'\\xC7\\x06\\x00\\x1F\\x01\\x00')  # View 1
    a.j_near(b'\\xE9', 'redraw_all')
    a.label('not_dock_wifi')

    # Monitor icon around x=134 (132..158)
    a.emit(b'\\x81\\xFB\\x84\\x00')
    a.j_rel8(b'\\x72', 'not_dock_mon')
    a.emit(b'\\x81\\xFB\\x9E\\x00')
    a.j_rel8(b'\\x77', 'not_dock_mon')
    a.emit(b'\\xC7\\x06\\x00\\x1F\\x03\\x00')  # View 3
    a.j_near(b'\\xE9', 'redraw_all')
    a.label('not_dock_mon')
    a.j_near(b'\\xE9', 'event_loop')

    a.label('check_icon_click')
    # Desktop icon clicks:
    a.emit(b'\\x8B\\x1E\\x02\\x1F\\x8B\\x0E\\x04\\x1F') # BX=x, CX=y

    # If Col 2, Wi-Fi icon: x in [180..300], y in [130..165] -> View 1 (Wi-Fi)
    a.emit(b'\\x81\\xFB\\xB4\\x00')
    a.j_rel8(b'\\x72', 'not_icon_wifi')
    a.emit(b'\\x81\\xFB\\x2C\\x01')
    a.j_rel8(b'\\x77', 'not_icon_wifi')
    a.emit(b'\\x81\\xF9\\x82\\x00')
    a.j_rel8(b'\\x72', 'not_icon_wifi')
    a.emit(b'\\x81\\xF9\\xA5\\x00')
    a.j_rel8(b'\\x77', 'not_icon_wifi')
    a.emit(b'\\xC7\\x06\\x00\\x1F\\x01\\x00')  # View 1
    a.j_near(b'\\xE9', 'redraw_all')
    a.label('not_icon_wifi')

    # If Col 1, Sys Monitor: x in [14..160], y in [130..165] -> View 3 (Monitor)
    a.emit(b'\\x81\\xFB\\x0E\\x00')
    a.j_rel8(b'\\x72', 'not_icon_mon')
    a.emit(b'\\x81\\xFB\\xA0\\x00')
    a.j_rel8(b'\\x77', 'not_icon_mon')
    a.emit(b'\\x81\\xF9\\x82\\x00')
    a.j_rel8(b'\\x72', 'not_icon_mon')
    a.emit(b'\\x81\\xF9\\xA5\\x00')
    a.j_rel8(b'\\x77', 'not_icon_mon')
    a.emit(b'\\xC7\\x06\\x00\\x1F\\x03\\x00')  # View 3
    a.j_near(b'\\xE9', 'redraw_all')
    a.label('not_icon_mon')

    # If Col 1, Hardware: x in [14..160], y in [315..355] -> View 2 (Hardware)
    a.emit(b'\\x81\\xFB\\x0E\\x00')
    a.j_rel8(b'\\x72', 'not_icon_hw')
    a.emit(b'\\x81\\xFB\\xA0\\x00')
    a.j_rel8(b'\\x77', 'not_icon_hw')
    a.emit(b'\\x81\\xF9\\x3B\\x01')
    a.j_rel8(b'\\x72', 'not_icon_hw')
    a.emit(b'\\x81\\xF9\\x63\\x01')
    a.j_rel8(b'\\x77', 'not_icon_hw')
    a.emit(b'\\xC7\\x06\\x00\\x1F\\x02\\x00')  # View 2
    a.j_near(b'\\xE9', 'redraw_all')
    a.label('not_icon_hw')

    a.j_near(b'\\xE9', 'event_loop')"""

assert old_section in text, 'old_section not found'
text = text.replace(old_section, new_section)

with open(r'C:\Users\barua\.gemini\antigravity\scratch\micro-os\scripts\build_clean_interactive_os.py', 'w') as f:
    f.write(text)

print('Clean click handler applied!')
