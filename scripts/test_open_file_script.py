from json import load as jload

base_url = "../default_data"

def test_open_file_script():
    print("Opening file...")
    with open(base_url + "/default_prize_statuses.json") as f:
        data = jload(f)
    print("File opened successfully.")
    print(data)

test_open_file_script()