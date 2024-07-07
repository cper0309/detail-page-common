import requests
from bs4 import BeautifulSoup

def fetch_page(url):
    # 언어를 한국어로 설정하기 위해 URL에 파라미터 추가
    if '?' in url:
        url += '&l=koreana'
    else:
        url += '?l=koreana'

    response = requests.get(url)
    if response.status_code != 200:
        raise Exception(f"Failed to load page: Status code {response.status_code}")
    return response.text

def parse_page(html):
    soup = BeautifulSoup(html, 'html.parser')

    # 게임 설명 영역 추출
    description_section = soup.find('div', id='game_area_description')
    if not description_section:
        raise Exception("Required sections (game_area_description) not found in the HTML")

    description_html = str(description_section)

    # 시스템 요구 사항 영역 추출
    sys_req_section = soup.find('div', class_='game_page_autocollapse sys_req')
    if not sys_req_section:
        raise Exception("Required sections (game_page_autocollapse sys_req) not found in the HTML")

    sys_req_html = str(sys_req_section)

    # 두 번째 동영상 URL 추출
    video_section = soup.find('div', id='highlight_player_area')
    video_url = None
    if video_section:
        videos = video_section.find_all('div', class_='highlight_player_item highlight_movie')
        if len(videos) > 1 and 'data-mp4-source' in videos[1].attrs:
            video_url = videos[1]['data-mp4-source']

    return description_html, sys_req_html, video_url

def style_html_content(description_html, sys_req_html):
    description_soup = BeautifulSoup(description_html, 'html.parser')
    sys_req_soup = BeautifulSoup(sys_req_html, 'html.parser')

    # 게임 설명 영역 스타일 설정
    for element in description_soup.find_all():
        if element.name not in ['h2', 'u', 'img']:
            element['style'] = 'font-size: 12pt; text-align: center; width: 90%; margin: 20pt auto;'

    # 시스템 요구 사항 영역 스타일 설정
    sys_req_div = sys_req_soup.find('div', class_='game_page_autocollapse sys_req')
    if sys_req_div:
        sys_req_div['style'] = 'width: 40%; margin: 20pt auto; text-align: justify;'

    for element in sys_req_soup.find_all():
        if element.name not in ['h2', 'u', 'img', 'div']:
            element['style'] = 'font-size: 12pt;'

    # "최소"와 "권장" 텍스트 스타일 설정 및 불필요한 태그 제거
    for element in sys_req_soup.find_all(string=lambda text: "최소:" in text or "권장:" in text):
        parent = element.parent
        new_tag = sys_req_soup.new_tag('span')
        new_tag['style'] = 'font-size: 14pt; font-weight: bold; display: block; margin-top: 15px; margin-bottom: -15px;'
        new_text = element.replace(':', '').strip()
        new_tag.string = new_text
        element.replace_with(new_tag)

    # h2 태그 스타일 설정
    for h2 in description_soup.find_all('h2') + sys_req_soup.find_all('h2'):
        h2['style'] = 'font-size: 20pt; font-weight: bold; text-align: center; width: 90%; margin: 10pt auto;'

    # u 태그 스타일 설정
    for u in description_soup.find_all('u') + sys_req_soup.find_all('u'):
        u['style'] = 'font-size: 15pt; text-align: center; width: 90%; margin: 10pt auto;'

    # img 태그 스타일 설정
    for img in description_soup.find_all('img') + sys_req_soup.find_all('img'):
        img['style'] = 'width: 90%; height: auto; margin: 20px auto;'

    return str(description_soup), str(sys_req_soup)

def create_html_page(video_url, styled_description_html, styled_sys_req_html, images, output_path='detailed_page.html'):
    # 비디오 HTML 생성
    video_html = f"""
    <div style="width: 90%; margin: 20px auto; text-align: center;">
        <video controls autoplay style="width: 100%;">
            <source src="{video_url}" type="video/mp4">
            Your browser does not support the video tag.
        </video>
    </div>
    """ if video_url else ""

    # 이미지 HTML 생성
    image_html = ""
    for image in images:
        image_html += f'<div style="text-align: center;"><img src="{image}" style="width: 90%;"></div>\n'

    # HTML template
    html_template = f"""
    <!DOCTYPE html>
    <html lang="ko">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Game Detail Page</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                margin: 20px;
                background-color: #1b2838;
                color: #c6d4df;
                text-align: center;
                font-size: 12pt;
            }}
            .content {{
                width: 85%;
                margin: 0 auto;
            }}
            img {{
                max-width: 90%;
                height: auto;
                display: block;
                margin: 20px auto;
            }}
            h2 {{
                color: #66c0f4;
                font-size: 20pt;
                font-weight: bold;
                text-align: center;
                width: 90%;
                margin: 10pt auto;
            }}
            u {{
                text-decoration: underline;
                font-size: 15pt;
                display: block;
                margin: 20px 0;
                text-align: center;
                width: 90%;
                margin: 10pt auto;
            }}
        </style>
    </head>
    <body>
        {image_html}
        {video_html}
        <div class="content">
            {styled_description_html}
        </div>
        <div class="content">
            {styled_sys_req_html}
        </div>
    </body>
    </html>
    """
    with open(output_path, 'w', encoding='utf-8') as file:
        file.write(html_template)

def fetch_images_from_github(github_url):
    response = requests.get(github_url)
    if response.status_code != 200:
        raise Exception("Failed to fetch GitHub URL")

    soup = BeautifulSoup(response.content, 'html.parser')
    base_url = "https://raw.githubusercontent.com/"
    user_repo_path = github_url.split("github.com/")[1].split("/tree/")[0]
    branch_path = github_url.split("/tree/")[1]

    images = set()  # 이미지를 중복 없이 저장하기 위해 set 사용
    for link in soup.find_all('a', href=True):
        if link['href'].endswith(('.png', '.jpg', '.jpeg', '.gif')):
            raw_image_url = f"{base_url}{user_repo_path}/{branch_path}/{link['href'].split('/')[-1]}"
            images.add(raw_image_url)

    images = sorted(images)  # 이름 순서대로 정렬
    return images

def main(url, github_url, output_path='detailed_page.html'):
    html = fetch_page(url)
    description_html, sys_req_html, video_url = parse_page(html)
    styled_description_html, styled_sys_req_html = style_html_content(description_html, sys_req_html)
    images = fetch_images_from_github(github_url)
    create_html_page(video_url, styled_description_html, styled_sys_req_html, images, output_path)

if __name__ == '__main__':
    url = 'https://store.steampowered.com/app/1623730/Palworld/'
    github_url = 'https://github.com/cper0309/detail-page-common/tree/main/detail-page-v1-240707'
    output_file_name = 'palworld'
    main(url, github_url, output_path=f"{output_file_name}.html")