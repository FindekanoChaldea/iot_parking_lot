# def upload_record(api_key, plate_license, entry_time, payment_time, exit_time, total_payment):
#     url = "https://api.thingspeak.com/update"
#     payload = {
#         "api_key": api_key,
#         "field1": plate_license,
#         "field2": entry_time,
#         "field3": payment_time,
#         "field4": exit_time,
#         "field5": total_payment
#     }

#     response = requests.post(url, data=payload)
#     if response.status_code == 200 and response.text != '0':
#         print(f"ThingSpeak uoload successfully，Entry ID: {response.text}")
#     else:
#         print(f"Upload failed: {response.status_code}，返回内容: {response.text}")
