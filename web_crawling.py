from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from webdriver_manager.chrome import ChromeDriverManager
import os
import requests
import time
import json
import re
from urllib.parse import unquote, urlparse

# 검색어 설정
search_keyword = 'カービィ グッズ'

# 이미지 저장 경로
save_dir = r'C:\Users\SBA_USER\Downloads\kirby_images'
if not os.path.exists(save_dir):
    os.makedirs(save_dir)

# 크롬 옵션 설정
chrome_options = Options()
chrome_options.add_argument('--disable-blink-features=AutomationControlled')
chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
chrome_options.add_experimental_option('useAutomationExtension', False)
chrome_options.add_argument('--disable-web-security')
chrome_options.add_argument('--allow-running-insecure-content')
chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')

# 드라이버 설치 및 실행
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=chrome_options)

# 봇 감지 방지
driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

def safe_download(url, filepath, headers=None):
    """안전한 이미지 다운로드"""
    if headers is None:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'image/webp,image/apng,image/*,*/*;q=0.8',
            'Accept-Language': 'ko-KR,ko;q=0.9,en;q=0.8',
        }
    
    try:
        response = requests.get(url, headers=headers, timeout=15, stream=True)
        response.raise_for_status()
        
        # 파일 크기 확인 (너무 작으면 스킵)
        content_length = response.headers.get('content-length')
        if content_length and int(content_length) < 1024:  # 1KB 미만
            return False
            
        with open(filepath, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        return True
    except Exception as e:
        print(f"다운로드 실패: {e}")
        return False

def extract_image_urls_from_page_source():
    """페이지 소스에서 이미지 URL 추출"""
    page_source = driver.page_source
    
    # 다양한 패턴으로 이미지 URL 찾기
    patterns = [
        r'"ou":"([^"]+)"',  # Google Images의 원본 URL
        r'"ow":(\d+),"pt":"([^"]+)"',  # 다른 패턴
        r'https://[^"]*\.(?:jpg|jpeg|png|gif|webp)[^"]*',  # 직접 이미지 URL
    ]
    
    urls = set()
    for pattern in patterns:
        matches = re.findall(pattern, page_source)
        for match in matches:
            if isinstance(match, tuple):
                url = match[-1] if match else None
            else:
                url = match
                
            if url and url.startswith('http'):
                try:
                    decoded_url = unquote(url)
                    if any(ext in decoded_url.lower() for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp']):
                        urls.add(decoded_url)
                except:
                    pass
    
    return list(urls)

try:
    print("구글 이미지 검색 시작...")
    
    # 구글 이미지 검색
    search_url = f"https://www.google.com/search?q={search_keyword}&tbm=isch"
    driver.get(search_url)
    time.sleep(3)
    
    # 쿠키/개인정보 동의 처리
    try:
        accept_button = driver.find_element(By.XPATH, "//button[contains(text(), 'Accept') or contains(text(), '모두 허용') or contains(text(), 'すべて同意')]")
        accept_button.click()
        time.sleep(2)
    except:
        pass
    
    print("이미지 로딩을 위해 스크롤링...")
    
    # 스크롤하면서 더 많은 이미지 로드
    for i in range(10):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)
        
        # "결과 더보기" 버튼 클릭 시도
        try:
            show_more = driver.find_element(By.CSS_SELECTOR, "input[value*='결과 더보기'], input[value*='Show more'], input[value*='もっと見る']")
            if show_more.is_displayed():
                driver.execute_script("arguments[0].click();", show_more)
                time.sleep(3)
                print("더 많은 결과 로드됨")
        except:
            pass
    
    print("페이지에서 이미지 URL 추출 중...")
    
    # 방법 1: 페이지 소스에서 URL 추출
    image_urls = extract_image_urls_from_page_source()
    print(f"페이지 소스에서 {len(image_urls)}개 URL 발견")
    
    # 방법 2: 썸네일 클릭해서 원본 이미지 찾기
    if len(image_urls) < 50:
        print("썸네일 클릭으로 추가 이미지 수집...")
        
        thumbnails = driver.find_elements(By.CSS_SELECTOR, "img")
        
        for i, thumb in enumerate(thumbnails[:50]):
            try:
                # 이미지가 보이는 영역으로 스크롤
                driver.execute_script("arguments[0].scrollIntoView(true);", thumb)
                time.sleep(0.5)
                
                # 썸네일 클릭
                ActionChains(driver).move_to_element(thumb).click().perform()
                time.sleep(1)
                
                # 큰 이미지 찾기
                large_imgs = driver.find_elements(By.CSS_SELECTOR, "img")
                for img in large_imgs:
                    src = img.get_attribute("src")
                    if src and src.startswith("http") and "gstatic" not in src:
                        if any(ext in src.lower() for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp']):
                            image_urls.add(src)
                
                if i % 10 == 0:
                    print(f"진행률: {i}/{min(50, len(thumbnails))}")
                    
            except Exception as e:
                continue
    
    image_urls = list(set(image_urls))[:100]  # 중복 제거 후 100개로 제한
    print(f"총 {len(image_urls)}개 이미지 URL 수집완료")
    
    # 이미지 다운로드
    success_count = 0
    
    for i, url in enumerate(image_urls):
        try:
            # 파일명 생성
            parsed_url = urlparse(url)
            extension = '.jpg'  # 기본 확장자
            
            if '.png' in url.lower():
                extension = '.png'
            elif '.gif' in url.lower():
                extension = '.gif'
            elif '.webp' in url.lower():
                extension = '.webp'
            
            filename = f"kirby_{i+1:03d}{extension}"
            filepath = os.path.join(save_dir, filename)
            
            print(f"다운로드 중... ({i+1}/{len(image_urls)}) {filename}")
            
            if safe_download(url, filepath):
                success_count += 1
                print(f"✓ 성공: {filename}")
            else:
                print(f"✗ 실패: {filename}")
                
        except Exception as e:
            print(f"✗ 에러 ({i+1}): {e}")
        
        time.sleep(0.5)  # 서버 부하 방지
    
    print(f"\n=== 완료 ===")
    print(f"성공: {success_count}개")
    print(f"실패: {len(image_urls) - success_count}개")
    print(f"저장 위치: {save_dir}")

except Exception as e:
    print(f"전체 프로세스 에러: {e}")
    print("문제가 계속되면 다른 방법을 시도해보세요.")

finally:
    driver.quit()

print("\n=== 추가 팁 ===")
print("1. 헤드리스 모드를 비활성화해서 브라우저 동작을 직접 확인해보세요")
print("2. 다른 검색 사이트나 API 사용을 고려해보세요")
print("3. VPN을 사용하면 차단을 우회할 수 있습니다")