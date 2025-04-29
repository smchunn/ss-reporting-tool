import httpx

def list_workspaces(access_token):
    url = "https://api.smartsheet.com/2.0/workspaces"
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    response = httpx.get(url, headers=headers)
    if response.status_code == 200:
        workspaces = response.json().get("data", [])
        for workspace in workspaces:
            print(f"Workspace Name: {workspace['name']}, Workspace ID: {workspace['id']}")
    else:
        print("Error:", response.status_code, response.text)

# Example usage
list_workspaces(
    access_token="8MFPPT7UqCkwTCZWxbriiNxaHpCbY6ieostnu"
)
