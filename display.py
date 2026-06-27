import time
import pygetwindow as gw

def log_active_window():
    print("Monitoring active windows... Press Ctrl+C to stop.\n")
    last_window = ""
    
    while True:
        try:
            # Get the currently focused window
            active_window = gw.getActiveWindow()
            
            if active_window and active_window.title:
                current_title = active_window.title
                
                # Only log if the window has changed to avoid spamming the console
                if current_title != last_window:
                    print(f"[ACTIVE WINDOW]: {current_title}")
                    last_window = current_title
                    
        except Exception as e:
            print(f"Error reading window title: {e}")
            
        time.sleep(5)

if __name__ == "__main__":
    log_active_window()