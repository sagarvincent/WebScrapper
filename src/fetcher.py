import requests

def fetch_html(url, output_file):
    response = requests.get(url)
    if response.status_code == 200:
        with open(output_file, 'w', encoding='utf-8') as file:
            file.write(response.text)
        print(f"HTML content saved to {output_file}")
    else:
        print(f"Failed to fetch HTML content. Status code: {response.status_code}")

if __name__ == "__main__":
    url = "http://example.com"  # Replace with your target URL
    output_file = "output.html"
    fetch_html(url, output_file)
