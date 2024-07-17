import os
import git
import urllib.parse
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow

# GitHub設定
REPO_PATH = "/Users/kikuchishun/ebay-images"
GITHUB_REPO_URL = "https://github.com/shun-awiiin/ebay-images.git"
IMAGE_FOLDER = "images"

# Google Sheets設定
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
SPREADSHEET_ID = '1gsQMlkcMCqPmstZIW7Jjfrwrx_GjB_WnplL7sEK7XMg'
RANGE_NAME = 'GPT画像!A:D'  # A列から D列までを含む

def setup_github_repo():
    if not os.path.exists(REPO_PATH):
        repo = git.Repo.clone_from(GITHUB_REPO_URL, REPO_PATH)
    else:
        repo = git.Repo(REPO_PATH)
    return repo

def copy_images_to_repo(source_folder):
    dest_folder = os.path.join(REPO_PATH, IMAGE_FOLDER)
    if not os.path.exists(dest_folder):
        os.makedirs(dest_folder)
    for filename in os.listdir(source_folder):
        if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp')):
            source_file = os.path.join(source_folder, filename)
            dest_file = os.path.join(dest_folder, filename)
            os.replace(source_file, dest_file)

def commit_and_push(repo):
    repo.git.add(A=True)
    repo.index.commit("Add new images")
    origin = repo.remote(name='origin')
    origin.push()

def generate_image_urls(github_username, repo_name):
    base_url = f"https://{github_username}.github.io/{repo_name}/"
    image_urls = {}
    image_folder_path = os.path.join(REPO_PATH, IMAGE_FOLDER)
    for filename in os.listdir(image_folder_path):
        if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp')):
            encoded_filename = urllib.parse.quote(filename)
            url = base_url + IMAGE_FOLDER + "/" + encoded_filename
            image_urls[filename] = url
    return image_urls

def get_google_sheets_service():
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    return build('sheets', 'v4', credentials=creds)

def update_spreadsheet(service, image_urls):
    # スプレッドシートからデータを取得
    result = service.spreadsheets().values().get(
        spreadsheetId=SPREADSHEET_ID, range=RANGE_NAME).execute()
    rows = result.get('values', [])

    # URLを更新
    for i, row in enumerate(rows):
        if i == 0:  # ヘッダー行をスキップ
            continue
        if len(row) > 0:
            filename = row[0]  # PicURL列の値（ファイル名）
            if filename in image_urls:
                if len(row) < 4:
                    row.extend([''] * (4 - len(row)))  # 必要に応じて列を追加
                row[3] = image_urls[filename]  # D列（インデックス3）にURLを設定

    # 更新されたデータをスプレッドシートに書き込む
    body = {'values': rows}
    result = service.spreadsheets().values().update(
        spreadsheetId=SPREADSHEET_ID, range=RANGE_NAME,
        valueInputOption='USER_ENTERED', body=body).execute()
    print(f"{result.get('updatedCells')} cells updated.")

def main():
    source_folder = "/Users/kikuchishun/ebay_test/Photoroom 2"
    github_username = "shun-awiiin"
    repo_name = "ebay-images"

    repo = setup_github_repo()
    copy_images_to_repo(source_folder)
    commit_and_push(repo)
    image_urls = generate_image_urls(github_username, repo_name)
    
    sheets_service = get_google_sheets_service()
    update_spreadsheet(sheets_service, image_urls)

if __name__ == "__main__":
    main()