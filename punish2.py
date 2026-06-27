import time
import os
import winsound

def trigger_audio_alarm():
    print("🔊 Playing un-mutable alarm for 60 seconds...")
    end_time = time.time() + 60  # Run for 60 seconds
    
    while time.time() < end_time:
        try:
            # Native Windows command to unmute and max out master volume
            # (Runs silently in the background)
            os.system("powershell -Command \"(New-Object -ComObject Wscript.Shell).SendKeys([char]175)\"")
            
            # Play a sharp, distinct system exclamation sound asynchronously
            winsound.PlaySound("SystemExclamation", winsound.SND_ALIAS | winsound.SND_ASYNC)
        except Exception as e:
            print(f"Audio Error: {e}")
            
        time.sleep(1)
    print("⏰ Alarm finished.")

# --- STANDALONE TEST BLOCK ---
# This allows you to run this file directly to test the sound
if __name__ == "__main__":
    print("Testing punish2.py independently...")
    trigger_audio_alarm()