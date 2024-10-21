import requests
import logging
import time
import configparser


class NodePayAPI:
    def __init__(self, base_url, log_file, api_key):
        self.base_url = base_url
        self.session = requests.Session()
        self.logger = self._setup_logger(log_file)
        self.api_key = api_key
        self.solve_url = "http://2captcha.com/in.php"
        self.result_url = "http://2captcha.com/res.php"

    def _setup_logger(self, log_file):
        logger = logging.getLogger("NodePayAPI")
        handler = logging.FileHandler(log_file)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        return logger

    def register(self, email, password, username, recaptcha_token=None, referral_code=None):
        data = {
            "email": email,
            "password": password,
            "recaptcha_token": recaptcha_token or self.solve_captcha(self.base_url + "register"),
            "referral_code": referral_code,
            "username": username
        }

        return self._send_request("register", data)

    def login(self, email, password, recaptcha_token=None, remember_me=True):
        data = {
            "email": email,
            "password": password,
            "recaptcha_token": recaptcha_token or self.solve_captcha(self.base_url + "login"),
            "remember_me": remember_me
        }

        return self._send_request("login", data)

    def _send_request(self, endpoint, data):
        headers = {
            "Accept": "*/*",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Accept-Language": "ru-RU,ru;q=0.8,en-US;q=0.5,en;q=0.3",
            "Connection": "keep-alive",
            "Content-Type": "application/json",
            "Origin": "https://app.nodepay.ai",
            "Referer": "https://app.nodepay.ai/",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:131.0) Gecko/20100101 Firefox/131.0"
        }

        try:
            url = f"{self.base_url}{endpoint}"
            response = self.session.post(url, headers=headers, json=data)
            self.logger.info(f"Sent POST request to {endpoint}: {data}")
            response.raise_for_status()
            self.logger.info(f"Response: {response.json()}")
            return response.json()
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Request failed: {e}")
            return None

    def solve_captcha(self, url):
        site_key = "6LdvcaMpAAAAACOZ6vyOh-V5zyl56NwvseDsWrH_"
        data = {
            'key': self.api_key,
            'method': 'userrecaptcha',
            'googlekey': site_key,  
            'pageurl': url,
            'json': 1
        }
        
        response = requests.post(self.solve_url, data=data)
        captcha_id = response.json().get('request')

        print(captcha_id) #Если выводит ERROR_ZERO_BALANCE - недостаточно средств на счету 2captcha.com
        
        time.sleep(20)

        result_data = {
            'key': self.api_key,
            'action': 'get',
            'id': captcha_id,
            'json': 1
        }

        for _ in range(10):
            result_response = requests.get(self.result_url, params=result_data)
            result = result_response.json()

            if result['status'] == 1:  
                return result['request']
            
            time.sleep(5) 

        raise Exception("Captcha solving failed")


def load_config(file_path):
    config = configparser.ConfigParser()
    config.read(file_path)
    return config


if __name__ == "__main__":
    config = load_config('settings.ini')

    email = config['auth']['email']
    password = config['auth']['password']
    username = config['auth']['username']
    api_key = config['auth']['api_key']
    referral_code = config['auth'].get('referral_code', None)
    remember_me = config['options'].getboolean('remember_me')

    base_url = config['server']['base_url']
    log_file = config['server']['log_file']

    api = NodePayAPI(base_url, log_file, api_key)

    action = input("Выберите действие (register/login): ").strip().lower()

    if action == "register":
        response = api.register(email, password, username, referral_code=referral_code)
    elif action == "login":
        response = api.login(email, password, remember_me=remember_me)
    else:
        print("Неверный выбор действия.")

        
        

       