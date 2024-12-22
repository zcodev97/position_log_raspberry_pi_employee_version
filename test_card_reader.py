import time
from card_reader_handler import initialize_card_reader, listen_for_card_swipe
from multiprocessing import Value

def test_card_reader():
    print("Initializing card reader...")
    card_reader = initialize_card_reader()
    
    if not card_reader:
        print("Failed to initialize card reader. Please check the connection.")
        return

    print("Card reader initialized successfully.")
    
    latest_card_data = Value('c', b'{}')
    
    print("Starting to listen for card swipes...")
    print("Please swipe a card now.")
    
    try:
        while True:
            listen_for_card_swipe(card_reader, None, latest_card_data)
            card_data = latest_card_data.value.decode()
            if card_data != '{}':
                print(f"Card swiped! Data: {card_data}")
                latest_card_data.value = b'{}'
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("Test ended by user.")
    finally:
        if hasattr(card_reader, 'cleanup'):
            card_reader.cleanup()

if __name__ == "__main__":
    test_card_reader()