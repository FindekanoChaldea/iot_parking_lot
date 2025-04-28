import random
import string
import json
import os 

def generate_plate():
    # Format: 3 letters, 3 digits, 2 letters
    letters = ''.join(random.choices(string.ascii_uppercase, k=3))  # 3 uppercase letters
    digits = ''.join(random.choices(string.digits, k=3))            # 3 digits
    end_letters = ''.join(random.choices(string.ascii_uppercase, k=2))  # 2 more letters

    return f"{letters}{digits}{end_letters}"
n = 1
plates = []
while n < 100:
    car = generate_plate()
    plates.append(car)
    n += 1

path = os.path.dirname(os.path.abspath(__file__))
if len(plates) == len(set(plates)):
    with open(f'{path}/fake_cars.json', 'w') as fp:
	    json.dump(plates, fp)