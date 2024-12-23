import time
import serial
import adafruit_pn532.uart
import winsound
from datetime import datetime
import tkinter as tk
from tkinter import ttk
import threading

class CardReaderGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("NFC Card Reader")
        self.root.geometry("400x300")
        
        # Create GUI elements
        self.status_label = ttk.Label(root, text="Waiting for card...", font=('Arial', 12))
        self.status_label.pack(pady=20)
        
        self.card_id_label = ttk.Label(root, text="Card ID: ", font=('Arial', 12))
        self.card_id_label.pack(pady=10)
        
        self.last_read_label = ttk.Label(root, text="Last Read: Never", font=('Arial', 12))
        self.last_read_label.pack(pady=10)
        
        # Initialize NFC reader
        self.init_nfc_reader()
        
        # Start reading thread
        self.running = True
        self.reader_thread = threading.Thread(target=self.read_card_loop, daemon=True)
        self.reader_thread.start()

    def init_nfc_reader(self):
        try:
            serial_port = 'COM6'
            baudrate = 115200
            uart = serial.Serial(serial_port, baudrate=baudrate, timeout=1)
            self.pn532 = adafruit_pn532.uart.PN532_UART(uart, debug=False)
            
            ic, ver, rev, support = self.pn532.firmware_version
            self.status_label.config(text=f"Reader initialized\nFirmware: {ver}.{rev}")
            self.pn532.SAM_configuration()
        except Exception as e:
            self.status_label.config(text=f"Error initializing reader:\n{str(e)}")

    def read_card_loop(self):
        while self.running:
            try:
                uid = self.pn532.read_passive_target(timeout=0.5)
                if uid is not None:
                    # Convert UID to string format
                    uid_string = ''.join([format(i, '02X') for i in uid])
                    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    
                    # Update GUI (thread-safe)
                    self.root.after(0, self.update_gui, uid_string, current_time)
                    winsound.Beep(1000, 500)
                    time.sleep(1)
            except Exception as e:
                self.root.after(0, self.status_label.config, {"text": f"Error: {str(e)}"})
                time.sleep(1)

    def update_gui(self, uid_string, current_time):
        self.status_label.config(text="Card Detected!", foreground="green")
        self.card_id_label.config(text=f"Card ID: {uid_string}")
        self.last_read_label.config(text=f"Last Read: {current_time}")

    def on_closing(self):
        self.running = False
        self.root.destroy()

def main():
    root = tk.Tk()
    app = CardReaderGUI(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()

if __name__ == "__main__":
    main()
