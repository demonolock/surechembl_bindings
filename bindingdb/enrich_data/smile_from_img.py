import requests

def get_smiles_from_image(image_url, api_url="https://api.mathpix.com/v3/text", app_id=None, app_key=None):
    """
    :param image_url: URL to the image
    :param api_url: API endpoint
    :param app_id: (optional) Mathpix app_id
    :param app_key: (optional) Mathpix app_key
    :return: SMILES string or None
    """
    headers = {
        "Content-Type": "application/json",
    }
    if app_id and app_key:
        headers["app_id"] = app_id
        headers["app_key"] = app_key

    payload = {
        "src": image_url,
        "formats": ["text", "data", "html"],
        "include_smiles": True
    }

    response = requests.post(api_url, json=payload, headers=headers)
    if response.ok:
        data = response.json()
        smiles = data.get("text")
        print(f"SMILES: {smiles}")
        return smiles
    else:
        print("Request failed:", response.status_code, response.text)
        return None

# Example usage:
image_url = "https://surechembl.org/api/assets/attachment/285192664/EP/20141210/A1/000002/81/09/38/imgb0011.tif"
# If using Mathpix, set your credentials:
# smiles = get_smiles_from_image(image_url, app_id="your_app_id", app_key="your_app_key")
smiles = get_smiles_from_image(image_url)
print(smiles)
