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

ena = 2

direction_pin1 = 3
pulse_pin1 = 4

direction_pin2 = 17
pulse_pin2 = 27

direction_pin3 = 22
pulse_pin3 = 10

direction_pin4 = 9
pulse_pin4 = 11

direction_pin5 = 5
pulse_pin5 = 6

direction_pin6 = 13
pulse_pin6 = 19

direction_pin7 = 26
pulse_pin7 = 21

direction_pin8 = 20
pulse_pin8 = 16

direction_pin9 = 12
pulse_pin9 = 7

direction_pin10 = 8
pulse_pin10 = 25

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

cw_direction = 0
ccw_direction = 1

gpio.setmode(gpio.BCM)
gpio.setwarnings(False)
gpio.setup(ena, gpio.OUT)
gpio.output(ena, gpio.HIGH)

gpio.setup(direction_pin3, gpio.OUT)
gpio.setup(pulse_pin3, gpio.OUT)
gpio.output(direction_pin3, cw_direction)

gpio.setup(direction_pin1, gpio.OUT)
gpio.setup(pulse_pin1, gpio.OUT)
gpio.output(direction_pin1, cw_direction)

gpio.setup(direction_pin2, gpio.OUT)
gpio.setup(pulse_pin2, gpio.OUT)
gpio.output(direction_pin2, cw_direction)

def reste_optimal(somme, pieces_disponibles):
    pieces_disponibles = sorted(pieces_disponibles, reverse=True)
    reste = somme
    reste_pieces = []
    for piece in pieces_disponibles:
        while reste >= piece:
            reste_pieces.append(piece)
            reste = round(reste - piece, 2)
    if reste > 0:
        reste_pieces.append(round(reste, 2))
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

def dispenceitm(direction_pin, pulse_pin):
    gpio.output(ena, gpio.LOW)
    print('MOTOR1')
    sleep(.5)
    gpio.output(direction_pin, cw_direction)
    for x in range(200):
        gpio.output(pulse_pin, gpio.HIGH)
        sleep(.001)
        gpio.output(pulse_pin, gpio.LOW)
        sleep(.0005)
    gpio.output(ena, gpio.HIGH)

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
        1: 0.1,
        2: 0.2,
        3: 0.5,
        4: 1,
        5: 2
    }
    pulse_count = 0
    last_pulse_time = 0
    wait_time = 2
    debounce_time = 0.1

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

def display_insert_coin_interface(product, token, button_number):
    global Money

    def update_coin_label():
        change = 0
        coins_info_label.config(text=f"Total Coins Inserted: {Money}")
        coins_info_label.after(1000, update_coin_label)
        product_price = float(product['price'].replace('â‚¬', '').strip())
        if Money == product_price:
            print("Product purchased successfully!")
            pins = pin_mappings.get(button_number)
            if pins:
                dispenceitm(pins['direction_pin'], pins['pulse_pin'])
                response = sell_product(product['id'], 1, "cash", token)
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
                response = sell_product(product['id'], 1, "cash", token)
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
                gpio.output(ena, gpio.LOW)
                if piece == 0.1:
                    turn_motor1(cw_direction)
                    sleep(1)
                    turn_motor1(ccw_direction)
                    sleep(0.5)
                elif piece == 0.5:
                    turn_motor1(ccw_direction)
                    sleep(1)
                    turn_motor1(cw_direction)
                    sleep(0.5)
                elif piece == 1:
                    turn_motor2(ccw_direction)
                    sleep(1)
                    turn_motor2(cw_direction)
                    sleep(0.5)
                elif piece == 2:
                    turn_motor2(cw_direction)
                    sleep(1)
                    turn_motor2(ccw_direction)
                    sleep(0.5)
            gpio.output(ena, gpio.HIGH)
            change = 0
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

    coins_info_label = Label(insert_coin_window, text="Total Coins Inserted: 0", font=("Arial", 12))
    coins_info_label.pack(pady=10)

    cancel_button = Button(insert_coin_window, text="Cancel", command=cancel_transaction)
    cancel_button.pack(pady=20)

    threading.Thread(target=count_coins, daemon=True).start()
    update_coin_label()

def create_interface():
    def on_button_click(product, button_number):
        display_insert_coin_interface(product, token, button_number)

    root = tk.Tk()
    root.title("Product Vending Machine")
    root.geometry("800x480")

    response = requests.get('http://127.0.0.1:8000/api/products')
    products = response.json()

    token = "YOUR_ACCESS_TOKEN"

    canvas = Canvas(root)
    canvas.pack(side="left", fill="both", expand=True)

    scrollbar = tk.Scrollbar(root, command=canvas.yview)
    scrollbar.pack(side="right", fill="y")

    canvas.configure(yscrollcommand=scrollbar.set)

    product_frame = tk.Frame(canvas)
    canvas.create_window((0, 0), window=product_frame, anchor="nw")

    for index, product in enumerate(products):
        image_url = product['image_url']
        image = load_image(image_url)
        label = tk.Label(product_frame, image=image, text=f"{product['name']}\nPrice: {product['price']}", compound="top")
        label.image = image
        label.grid(row=index // 4, column=index % 4, padx=10, pady=10)

        button = tk.Button(product_frame, text="Buy", command=lambda p=product, b=index: on_button_click(p, b))
        button.grid(row=index // 4 + 1, column=index % 4, padx=10, pady=10)

    product_frame.update_idletasks()
    canvas.config(scrollregion=canvas.bbox("all"))

    root.mainloop()

create_interface()
