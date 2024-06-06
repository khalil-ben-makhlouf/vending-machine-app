import tkinter as tk
from tkinter import Toplevel, Label, Button, Canvas, Entry, messagebox
from PIL import Image, ImageTk
import requests
from datetime import datetime
from io import BytesIO
import threading
import time
import RPi.GPIO as gpio
from time import sleep
import requests


Money = 0

ena=2

#coins return
direction_pin1   =3
pulse_pin1       = 4

direction_pin2   = 17
pulse_pin2       = 27


#itemreturn
direction_pin3   = 22
pulse_pin3       = 10

direction_pin4   = 9
pulse_pin4   = 11

direction_pin5   = 5
pulse_pin5       = 6

direction_pin6   = 13
pulse_pin6       = 19

direction_pin7   = 26
pulse_pin7       = 21

direction_pin8   = 20
pulse_pin8       = 16

direction_pin9   = 12
pulse_pin9       = 7

direction_pin10   = 8
pulse_pin10       = 25

# Define pin mappings
pin_mappings = {
    0: {'direction_pin': 22, 'pulse_pin': 10},
    1: {'direction_pin': 9, 'pulse_pin': 11},
    2: {'direction_pin': 5, 'pulse_pin': 6},
    3: {'direction_pin': 13, 'pulse_pin': 19},
    4: {'direction_pin': 26, 'pulse_pin': 21},
    5: {'direction_pin': 20, 'pulse_pin': 16},
    6: {'direction_pin': 12, 'pulse_pin': 7},
    7: {'direction_pin': 8, 'pulse_pin': 25},
}


cw_direction    = 0 
ccw_direction   = 1 

gpio.setmode(gpio.BCM)
gpio.setwarnings(False)
gpio.setup(ena, gpio.OUT)
gpio.output(ena,gpio.HIGH)

gpio.setup(direction_pin3, gpio.OUT)
gpio.setup(pulse_pin3, gpio.OUT)
gpio.output(direction_pin3,cw_direction)

gpio.setup(direction_pin1, gpio.OUT)
gpio.setup(pulse_pin1, gpio.OUT)
gpio.output(direction_pin1,cw_direction)

gpio.setup(direction_pin2, gpio.OUT)
gpio.setup(pulse_pin2, gpio.OUT)
gpio.output(direction_pin2,cw_direction)


def reste_optimal(somme, pieces_disponibles):
    pieces_disponibles = sorted(pieces_disponibles, reverse=True)
    reste = somme
    reste_pieces = []
    for piece in pieces_disponibles:
        while reste >= piece:
            reste_pieces.append(piece)
            reste = round(reste - piece, 2)  # Round to 2 decimal places
    if reste > 0:
        # If there's still some remainder left, add it to the list
        reste_pieces.append(round(reste, 2))  # Round to 2 decimal places
    return reste_pieces



def update_product_quantity(product_id, token):
    headers = {"Authorization": f"Bearer {token}"}
    update_url = f"http://127.0.0.1:8000/api/products/{product_id}/update_quantity"
    try:
        response = requests.patch(update_url, headers=headers)
        if response.status_code == 200:
            print(f"Product quantity updated successfully for product ID {product_id}")
        else:
            print(f"Failed to update product quantity for product ID {product_id}: {response.status_code}")
    except Exception as e:
        print(f"Error updating product quantity: {e}")


def dispenceitm(direction_pin,pulse_pin):
    gpio.output(ena,gpio.LOW)
    print('MOTOR1')
    sleep(.5)
    gpio.output(direction_pin,cw_direction)
    for x in range(200):
        gpio.output(pulse_pin,gpio.HIGH)
        sleep(.001)
        gpio.output(pulse_pin,gpio.LOW)
        sleep(.0005)
        
    gpio.output(ena,gpio.HIGH)


def turn_motor1(direction):
    gpio.output(direction_pin1, direction)
    for x in range(30):
        gpio.output(pulse_pin1, gpio.HIGH)
        sleep(.01)
        gpio.output(pulse_pin1, gpio.LOW)
        sleep(.01)

def turn_motor2(direction):
    
    gpio.output(direction_pin2, direction)
    for x in range(30):
        gpio.output(pulse_pin2, gpio.HIGH)
        sleep(.01)
        gpio.output(pulse_pin2, gpio.LOW)
        sleep(.01)

    
    
def count_coins():
    gpio.setmode(gpio.BCM)
    
    global Money

    coin_pin = 26
    gpio.setup(coin_pin, gpio.IN)

    coin_values = {
        1: 0.1,   # 100 frank
        2: 0.2,   # 200 frank
        3: 0.5,   # 500 frank
        4: 1,  # 1000 frank
        5: 2   # 2000 frank
    }

    pulse_count = 0
    last_pulse_time = 0

    wait_time = 2

    debounce_time = 0.1  # Adjust as needed

    def count_pulse(channel):
        nonlocal pulse_count, last_pulse_time
        current_time = time.time()
        if current_time - last_pulse_time > debounce_time:
            pulse_count += 1
            last_pulse_time = current_time

    gpio.add_event_detect(coin_pin, gpio.RISING, callback=count_pulse)

    try:
        while True:
            if time.time() - last_pulse_time >= wait_time and pulse_count > 0:
                print("Total Pulses:", pulse_count)
                Money += coin_values[pulse_count]
                pulse_count = 0  
            time.sleep(0.1)  

    except KeyboardInterrupt:
        gpio.cleanup()


def load_image(url):
    response = requests.get(url.strip())
    if response.status_code == 200:
        image_data = response.content
        image = Image.open(BytesIO(image_data))
        image.thumbnail((100, 100))  
        photo = ImageTk.PhotoImage(image)
        return photo
    else:
        print(f"Failed to load image: HTTP {response.status_code}")
        return None
    

def sell_product(product_id, quantity, payment_method, token):
    url = f'http://127.0.0.1:8000/api/products/{product_id}/sell'
    headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
    data = {'quantity': quantity, 'payment_method': payment_method}
    response = requests.post(url, json=data, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        return None

def display_insert_coin_interface(product,token, button_number):
    global Money

    def update_coin_label():
        change = 0
        coins_info_label.config(text=f"Total Coins Inserted: {Money}")
        coins_info_label.after(1000, update_coin_label)  # Update every second
        product_price = float(product['price'].replace('â‚¬', '').strip())  # Convert price string to float
        if Money == product_price:
            print("Product purchased successfully!")
            pins = pin_mappings.get(button_number)
            if pins:
                dispenceitm(pins['direction_pin'], pins['pulse_pin'])
                response = sell_product(product['id'], 1, "cash", token)  # Added "cash" as payment method
                if response:
                    print("Success", f"Product sold successfully! New quantity: {response['new_quantity']}")
                else:
                    print("Error", "Failed to sell product.")

            else:
                print(f"No pin mapping found for button number {button_number}")
            cancel_transaction()
        
            cancel_transaction()
        elif Money > product_price:
            if pins:
                dispenceitm(pins['direction_pin'], pins['pulse_pin'])
                response = sell_product(product['id'], 1, "cash", token)  # Added "cash" as payment method
                if response:
                    print("Success", f"Product sold successfully! New quantity: {response['new_quantity']}")
                else:
                    print("Error", "Failed to sell product.")
        
            sleep(1)
            change = round(Money - product_price, 1)
            print(f"Product purchased successfully! Change: {change} ")
            pieces_disponibles = [0.1, 0.5, 1, 2]
            reste_pieces = reste_optimal(change, pieces_disponibles)

            for piece in reste_pieces:
                gpio.output(ena,gpio.LOW)
                if piece == 0.1:
                    turn_motor1(cw_direction)  # Turn left
                    sleep(1)
                    turn_motor1(ccw_direction)  # Turn right
                    
                    sleep(0.5)
                elif piece == 0.5:
                    turn_motor1(ccw_direction)  # Turn left
                    sleep(1)
                    turn_motor1(cw_direction)            
                    sleep(0.5)
                elif piece == 1:
                    turn_motor2(ccw_direction)  # Turn right
                    sleep(1)
                    turn_motor2(cw_direction)  # Turn left
                    sleep(0.5)	                
                elif piece == 2:
                    turn_motor2(cw_direction)  # Turn right
                    sleep(1)
                    turn_motor2(ccw_direction)  # Turn left
                    sleep(0.5)
            gpio.output(ena, gpio.HIGH)
            

            change=0
            cancel_transaction()
            

    def cancel_transaction():
        global Money
        Money = 0
        insert_coin_window.destroy()

    insert_coin_window = Toplevel()
    insert_coin_window.title("Insert Coin")
    insert_coin_window.geometry("800x480")
    
    if button_number is not None:
        print(f"Button number {button_number} is pressed")

    product_name_label = Label(insert_coin_window, text=f"Product: {product['name']}", font=("Arial", 14))
    product_name_label.pack(pady=10)

    product_price_label = Label(insert_coin_window, text=f"Price: {product['price']} â‚¬", font=("Arial", 12))
    product_price_label.pack(pady=10)

    photo = load_image("http://127.0.0.1:8000/storage/" + product['image'].strip()) if 'image' in product else None
    if photo:
        image_label = Label(insert_coin_window, image=photo)
        image_label.image = photo
        image_label.pack(pady=10)
    else:
        print("Product image not found.")

    insert_coin_label = Label(insert_coin_window, text="Please insert coins", font=("Arial", 12))
    insert_coin_label.pack(pady=(10, 10))  

    coins_info_label = Label(insert_coin_window, text=f"Total Coins Inserted: {Money}", font=("Arial", 12))
    coins_info_label.pack(pady=(5, 10))
   


    # Start updating the coin label
    update_coin_label()

    cancel_button = Button(insert_coin_window, text="Cancel", command=cancel_transaction, bg="#007FFF", fg="white", font=("Arial", 12), padx=10, pady=5)
    cancel_button.pack(pady=10)



def create_product_button(parent_frame, product, coord, button_number,token):
    button = Button(parent_frame, borderwidth=0, highlightthickness=0)
    button.image = None  
    if 'image' in product:
        image_url = "http://127.0.0.1:8000/storage/" + product['image'].strip()
        photo = load_image(image_url)
        if photo:

            def on_button_click():
                thread = threading.Thread(target=display_insert_coin_interface, args=(product, token, button_number))
                thread.start()
            button.configure(image=photo, command=on_button_click)
            button.image = photo
        else:
            print("Failed to load image for product:", product["name"])
    else:
        print("Product image not found.")
    button.place(x=coord[0], y=coord[1])

    product_name_label = Label(parent_frame, text=product["name"], font=("Arial", 12))
    product_name_label.place(x=coord[0] , y=coord[1] + 110)

    product_price_label = Label(parent_frame, text=f"{product['price']} dt", font=("Arial", 10))
    product_price_label.place(x=coord[0] , y=coord[1] + 130)

    return button

def update_time(canvas, date_text_id, time_text_id):
    now = datetime.now()
    date_text = now.strftime("%A\n%d-%m-%y")
    time_text = now.strftime("%H:%M")
    canvas.itemconfig(date_text_id, text=date_text)
    canvas.itemconfig(time_text_id, text=time_text)
    canvas.after(60000, update_time, canvas, date_text_id, time_text_id)

def afficher_produits(token, root):
    headers = {"Authorization": "Bearer " + token}
    products_response = requests.get("http://127.0.0.1:8000/api/productsAPI", headers=headers)
    if products_response.status_code == 200:
        data = products_response.json()

        coordinates = [(15.0, 110.0),(179.5, 110.0),(355.0, 110.0),(500.0, 110.0),(650.0, 110.0),
                       (15.0, 300.0),(179.5, 300.0),(355.0, 300.0),(500.0, 300.0),(650.0, 300.0)]

        buttons = []
        for idx, coord in enumerate(coordinates):
            if idx < len(data):
                product = data[idx]
                product_name = product["name"]
                product_price = str(product["price"])
                print(product_price)
                
                if 'image' in product:
                    x, y = coord
                    button_number = idx
                    button = create_product_button(root, product, coord, button_number, token)
                    buttons.append(button)
                else:
                    print("Product image not found.")
    else:
        print("Failed to fetch products")

def login():
    email = email_entry.get()
    password = password_entry.get()

    login_response = requests.post("http://127.0.0.1:8000/api/login", data={"email": email, "password": password})

    if login_response.status_code == 200:
        token = login_response.json()["access_token"]
        login_window.destroy()
        display_main_interface(token)
    else:
        messagebox.showerror("Login Error", "No account found with these credentials.")

def display_main_interface(token):
    window = tk.Tk()
    window.title("Liste des produits")
    canvas = Canvas(window, width=800, height=480)
    canvas.pack()

    date_text_id = canvas.create_text(590.0, 20.0, anchor="nw", text="", fill="#5B148F", font=("Inter", 15))
    time_text_id = canvas.create_text(705.0, 30.0, anchor="nw", text="", fill="#5B148F", font=("Inter", 20))
    canvas.create_rectangle(
    0,
    92.0,
    800.0,
    95.0,
    fill="#000000",
    outline="")

    logo_image = Image.open(r"/home/ksi/Desktop/Frame 2.png")
    logo_image.thumbnail((200, 200))
    logo_photo = ImageTk.PhotoImage(logo_image)
    logo_id = canvas.create_image(
            124, 40,
            image=logo_photo
        )
    canvas.create_text(
        685.0,
        20.0,
        anchor="nw",
        text="|",
        fill="#5B148F",
        font=("Inter", 40 * -1)
    )
    
    afficher_produits(token, window)
    update_time(canvas, date_text_id, time_text_id)
    window.mainloop()

login_window = tk.Tk()
login_window.title("Login")
login_window.geometry("800x400")

login_window.configure(bg="#f0f0f0")

welcome_label = Label(login_window, text="Welcome to Your Vending Machine", bg="#f0f0f0", fg="#007FFF", font=("Arial", 16))
welcome_label.pack(pady=10)

message_label = Label(login_window, text="Please enter your appropriate credentials", bg="#f0f0f0", font=("Arial", 12))
message_label.pack(pady=5)

email_label = Label(login_window, text="Email:", bg="#f0f0f0", font=("Arial", 14))
email_label.place(x=200, y=200)
email_entry = Entry(login_window, font=("Arial", 14), width=20)
email_entry.place(x=350, y=200)

password_label = Label(login_window, text="Password:", bg="#f0f0f0", font=("Arial", 14))
password_label.place(x=200, y=250)
password_entry = Entry(login_window, show="*", font=("Arial", 14), width=20)
password_entry.place(x=350, y=250)

submit_button = Button(login_window, text="Submit", command=login, bg="#007FFF", fg="white", font=("Arial", 14), bd=0, padx=10, pady=5, highlightthickness=2, relief="solid")
submit_button.place(x=350, y=300)


coin_thread = threading.Thread(target=count_coins)
coin_thread.daemon = True  # Set as daemon so it will stop when the main thread stops
coin_thread.start()

login_window.mainloop()
