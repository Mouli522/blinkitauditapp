import flet as ft
from datetime import datetime
import time
import os
import wave
import math
import threading

# Generate a beep sound if it doesn't exist
def ensure_alarm_sound():
    os.makedirs("assets", exist_ok=True)
    file_path = os.path.join("assets", "alarm.wav")
    if not os.path.exists(file_path):
        sample_rate = 44100
        duration = 1.5 # seconds
        freq = 440.0 # Hz
        
        with wave.open(file_path, 'w') as obj:
            obj.setnchannels(1)
            obj.setsampwidth(2)
            obj.setframerate(sample_rate)
            
            # Generate a simple beep
            for i in range(int(sample_rate * duration)):
                # Sine wave
                value = int(32767.0 * math.sin(2.0 * math.pi * freq * i / sample_rate))
                # Add pulsing effect
                if (i // 10000) % 2 == 0:
                    data = value.to_bytes(2, byteorder='little', signed=True)
                    obj.writeframesraw(data)
                else:
                    obj.writeframesraw((0).to_bytes(2, byteorder='little', signed=True))

def main(page: ft.Page):
    ensure_alarm_sound()

    page.title = "Blinkit Utility App"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.theme = ft.Theme(
        color_scheme_seed=ft.colors.DEEP_PURPLE,
        visual_density=ft.ThemeVisualDensity.COMFORTABLE,
    )
    # Mobile UI adjustments
    page.window.width = 400
    page.window.height = 800
    page.padding = 0
    page.vertical_alignment = ft.MainAxisAlignment.START
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER

    alarm_sound = ft.Audio(src="alarm.wav", autoplay=False)
    page.overlay.append(alarm_sound)

    # --- Timer Section ---
    items_input = ft.TextField(
        label="Number of items",
        keyboard_type=ft.KeyboardType.NUMBER,
        icon=ft.icons.FORMAT_LIST_NUMBERED,
        border_radius=15,
        width=300
    )
    interval_input = ft.TextField(
        label="Interval (seconds)",
        keyboard_type=ft.KeyboardType.NUMBER,
        icon=ft.icons.TIMER,
        border_radius=15,
        width=300
    )
    
    timer_text = ft.Text("00:00", size=50, weight=ft.FontWeight.BOLD, color=ft.colors.DEEP_PURPLE)
    timer_progress = ft.ProgressRing(value=0, width=150, height=150, stroke_width=10)
    
    timer_state = {
        "running": False,
        "paused": False,
        "remaining_seconds": 0,
        "total_seconds": 0
    }
    
    def update_timer_ui():
        if timer_state["total_seconds"] > 0:
            mins, secs = divmod(timer_state["remaining_seconds"], 60)
            timer_text.value = f"{mins:02d}:{secs:02d}"
            timer_progress.value = (timer_state["total_seconds"] - timer_state["remaining_seconds"]) / timer_state["total_seconds"]
        else:
            timer_text.value = "00:00"
            timer_progress.value = 0
        page.update()

    def timer_thread():
        while timer_state["running"]:
            if not timer_state["paused"]:
                if timer_state["remaining_seconds"] > 0:
                    time.sleep(1)
                    if not timer_state["running"] or timer_state["paused"]:
                        break
                    timer_state["remaining_seconds"] -= 1
                    update_timer_ui()
                else:
                    # Timer finished
                    timer_state["running"] = False
                    alarm_sound.play()
                    start_btn.disabled = False
                    pause_btn.disabled = True
                    items_input.disabled = False
                    interval_input.disabled = False
                    update_timer_ui()
                    page.update()
                    break
            else:
                time.sleep(0.1)

    def start_timer(e):
        if timer_state["running"] and timer_state["paused"]:
            # Resume
            timer_state["paused"] = False
            pause_btn.text = "Pause"
            pause_btn.icon = ft.icons.PAUSE
            page.update()
            return

        if not items_input.value or not interval_input.value:
            page.open(ft.SnackBar(ft.Text("Please enter both items and interval!")))
            return
            
        try:
            items = int(items_input.value)
            interval = int(interval_input.value)
        except ValueError:
            page.open(ft.SnackBar(ft.Text("Please enter valid numbers!")))
            return
            
        timer_state["total_seconds"] = items * interval
        timer_state["remaining_seconds"] = timer_state["total_seconds"]
        timer_state["running"] = True
        timer_state["paused"] = False
        
        start_btn.disabled = True
        pause_btn.disabled = False
        pause_btn.text = "Pause"
        pause_btn.icon = ft.icons.PAUSE
        
        items_input.disabled = True
        interval_input.disabled = True
        
        update_timer_ui()
        threading.Thread(target=timer_thread, daemon=True).start()

    def pause_timer(e):
        if timer_state["running"]:
            timer_state["paused"] = not timer_state["paused"]
            if timer_state["paused"]:
                pause_btn.text = "Resume"
                pause_btn.icon = ft.icons.PLAY_ARROW
                start_btn.disabled = True
            else:
                pause_btn.text = "Pause"
                pause_btn.icon = ft.icons.PAUSE
                # Start a new thread to resume
                threading.Thread(target=timer_thread, daemon=True).start()
            page.update()

    def reset_timer(e):
        timer_state["running"] = False
        timer_state["paused"] = False
        timer_state["remaining_seconds"] = 0
        timer_state["total_seconds"] = 0
        
        start_btn.disabled = False
        pause_btn.disabled = True
        pause_btn.text = "Pause"
        pause_btn.icon = ft.icons.PAUSE
        
        items_input.disabled = False
        interval_input.disabled = False
        items_input.value = ""
        interval_input.value = ""
        
        update_timer_ui()

    start_btn = ft.ElevatedButton("Start", icon=ft.icons.PLAY_ARROW, on_click=start_timer, style=ft.ButtonStyle(padding=15))
    pause_btn = ft.ElevatedButton("Pause", icon=ft.icons.PAUSE, on_click=pause_timer, disabled=True, style=ft.ButtonStyle(padding=15))
    reset_btn = ft.ElevatedButton("Reset", icon=ft.icons.RESTART_ALT, on_click=reset_timer, style=ft.ButtonStyle(padding=15, color=ft.colors.RED))

    timer_view = ft.Container(
        content=ft.Column(
            controls=[
                ft.Text("Timer", size=28, weight=ft.FontWeight.W_800),
                items_input,
                interval_input,
                ft.Container(height=20),
                ft.Stack(
                    [
                        timer_progress,
                        ft.Container(
                            content=timer_text,
                            alignment=ft.alignment.center,
                            width=150,
                            height=150,
                        )
                    ],
                    alignment=ft.alignment.center,
                ),
                ft.Container(height=30),
                ft.Row([start_btn, pause_btn, reset_btn], alignment=ft.MainAxisAlignment.CENTER)
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        padding=20
    )

    # --- Shelf Life Calculator Section ---
    def date_formatted(dt):
        return dt.strftime("%Y-%m-%d") if dt else "Not selected"

    mfg_date_val = None
    cur_date_val = datetime.now()
    exp_date_val = None

    mfg_date_text = ft.Text(f"Mfg Date: {date_formatted(mfg_date_val)}", size=14)
    cur_date_text = ft.Text(f"Current Date: {date_formatted(cur_date_val)}", size=14)
    exp_date_text = ft.Text(f"Expiry Date: {date_formatted(exp_date_val)}", size=14)
    
    result_text = ft.Text("Enter dates to calculate shelf life.", size=16, weight=ft.FontWeight.W_500, color=ft.colors.BLUE_700, text_align=ft.TextAlign.CENTER)
    result_progress = ft.ProgressBar(value=0, width=300, color=ft.colors.GREEN, bgcolor=ft.colors.GREY_300)

    def calculate_shelf_life():
        if not mfg_date_val or not exp_date_val:
            return
            
        total_life = (exp_date_val - mfg_date_val).days
        consumed_life = (cur_date_val - mfg_date_val).days
        remaining_life = total_life - consumed_life
        
        if total_life <= 0:
            result_text.value = "Error: Expiry date must be after Mfg date."
            result_progress.value = 0
            page.update()
            return
            
        if consumed_life < 0:
            result_text.value = "Product not yet manufactured?"
            result_progress.value = 0
            page.update()
            return
            
        remaining_percentage = remaining_life / total_life
        
        # Color coding based on remaining life
        if remaining_percentage < 0.0:
            color = ft.colors.RED
            status = "EXPIRED"
            progress_val = 0.0
        elif remaining_percentage < 0.2:
            color = ft.colors.ORANGE
            status = f"Warning: Only {remaining_life} days left ({remaining_percentage*100:.1f}%)"
            progress_val = remaining_percentage
        else:
            color = ft.colors.GREEN
            status = f"Good: {remaining_life} days remaining ({remaining_percentage*100:.1f}%)"
            progress_val = remaining_percentage
            
        result_text.value = status
        result_text.color = color
        result_progress.value = progress_val
        result_progress.color = color
        page.update()

    def handle_mfg_date(e):
        nonlocal mfg_date_val
        mfg_date_val = e.control.value
        mfg_date_text.value = f"Mfg Date: {date_formatted(mfg_date_val)}"
        calculate_shelf_life()
        page.update()

    def handle_cur_date(e):
        nonlocal cur_date_val
        cur_date_val = e.control.value
        cur_date_text.value = f"Current Date: {date_formatted(cur_date_val)}"
        calculate_shelf_life()
        page.update()

    def handle_exp_date(e):
        nonlocal exp_date_val
        exp_date_val = e.control.value
        exp_date_text.value = f"Expiry Date: {date_formatted(exp_date_val)}"
        calculate_shelf_life()
        page.update()

    mfg_picker = ft.DatePicker(on_change=handle_mfg_date)
    cur_picker = ft.DatePicker(on_change=handle_cur_date, value=datetime.now())
    exp_picker = ft.DatePicker(on_change=handle_exp_date)
    
    page.overlay.extend([mfg_picker, cur_picker, exp_picker])

    def date_row(title, text_control, picker_control):
        return ft.Row(
            [
                ft.Icon(ft.icons.CALENDAR_MONTH, color=ft.colors.BLUE, size=20),
                ft.Container(content=text_control, expand=True, padding=ft.padding.only(left=10)),
                ft.IconButton(
                    icon=ft.icons.EDIT_CALENDAR,
                    icon_color=ft.colors.DEEP_PURPLE,
                    on_click=lambda _: page.open(picker_control),
                    tooltip=f"Pick {title}"
                )
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN
        )

    calc_view = ft.Container(
        content=ft.Column(
            controls=[
                ft.Text("Shelf Life Calculator", size=28, weight=ft.FontWeight.W_800),
                ft.Container(height=10),
                ft.Card(
                    elevation=4,
                    content=ft.Container(
                        padding=15,
                        width=320,
                        content=ft.Column([
                            date_row("Manufacturing Date", mfg_date_text, mfg_picker),
                            ft.Divider(height=2),
                            date_row("Current Date", cur_date_text, cur_picker),
                            ft.Divider(height=2),
                            date_row("Expiry Date", exp_date_text, exp_picker),
                        ], spacing=10)
                    )
                ),
                ft.Container(height=30),
                result_progress,
                ft.Container(height=10),
                result_text
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        padding=20
    )

    # --- Navigation ---
    main_content = ft.Container(content=timer_view, expand=True)

    def on_nav_change(e):
        if e.control.selected_index == 0:
            main_content.content = timer_view
        else:
            main_content.content = calc_view
        page.update()

    nav_bar = ft.NavigationBar(
        destinations=[
            ft.NavigationBarDestination(icon=ft.icons.TIMER, label="Timer"),
            ft.NavigationBarDestination(icon=ft.icons.CALCULATE, label="Shelf Life"),
        ],
        on_change=on_nav_change,
        selected_index=0
    )
    
    page.navigation_bar = nav_bar
    # Use a SafeArea for mobile displays so content isn't hidden behind notches/bars
    page.add(
        ft.SafeArea(
            content=main_content,
            expand=True
        )
    )

ft.app(target=main, assets_dir="assets")
