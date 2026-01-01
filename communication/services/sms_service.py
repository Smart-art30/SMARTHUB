def send_sms(phone_number, message):
    try:
        print(f"sendins SMS to {phone_number}: {message}")

        return True, None
    except Exeption as e:
        return False, str(e)