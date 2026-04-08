#!/usr/bin/env python3
"""
🚨 Attack Simulation Script for Educational Purposes
Только для демонстрации уязвимостей - НЕ ИСПОЛЬЗОВАТЬ В ЗЛОУМЫШЛЕННЫХ ЦЕЛЯХ
"""

import requests
import time
import itertools
import json
import re
from urllib.parse import urljoin
import warnings
warnings.filterwarnings('ignore')

class AttackSimulator:
    """Симулятор атак для тестирования безопасности"""
    
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.verify = False  # Игнорировать SSL для тестов
        
    def log_attack(self, attack_type, details):
        """Логирование попыток атаки"""
        print(f"[🚨 {attack_type}] {details}")
        
    def test_information_disclosure(self):
        """Тест на раскрытие информации"""
        self.log_attack("INFO_DISCLOSURE", "Проверка DEBUG=True")
        
        # Тест ошибки с DEBUG=True
        try:
            response = self.session.get(f"{self.base_url}/nonexistent-page/")
            if "DEBUG = True" in response.text or "Exception Location" in response.text:
                print("❌ CRITICAL: DEBUG=True в production - утечка информации")
                return True
        except:
            pass
            
        print("✅ DEBUG=False или информация скрыта")
        return False
        
    def test_default_admin_url(self):
        """Тест стандартного admin URL"""
        self.log_attack("DEFAULT_ADMIN", "Проверка /admin/")
        
        response = self.session.get(f"{self.base_url}/admin/")
        if response.status_code == 200:
            print("❌ WARNING: Стандартный admin URL доступен")
            return True
            
        print("✅ Admin URL изменен или защищен")
        return False
        
    def test_brute_force_login(self):
        """Симуляция brute force атаки"""
        self.log_attack("BRUTE_FORCE", "Пробуем популярные пароли")
        
        # Популярные пароли
        credentials = [
            ("admin", "admin"),
            ("admin", "password"),
            ("admin", "123456"),
            ("root", "root"),
            ("test", "test"),
            ("user", "password"),
            ("admin", "12345678"),
            ("administrator", "admin"),
        ]
        
        success_count = 0
        
        for username, password in credentials:
            try:
                # Получаем CSRF токен
                login_page = self.session.get(f"{self.base_url}/accounts/login/")
                csrf_match = re.search(r'name="csrfmiddlewaretoken" value="([^"]+)"', login_page.text)
                csrf_token = csrf_match.group(1) if csrf_match else ""
                
                # Пробуем войти
                response = self.session.post(f"{self.base_url}/accounts/login/", data={
                    'username': username,
                    'password': password,
                    'csrfmiddlewaretoken': csrf_token
                })
                
                if response.status_code == 302 and 'dashboard' in response.url:
                    print(f"❌ SUCCESS: {username}:{password} - УСПЕШНЫЙ ВХОД!")
                    success_count += 1
                    
            except Exception as e:
                print(f"Ошибка при попытке {username}:{password} - {e}")
                
        if success_count > 0:
            print(f"❌ CRITICAL: {success_count} аккаунтов скомпрометированы")
        else:
            print("✅ Brute force не удался (или все пароли сложные)")
            
        return success_count > 0
        
    def test_host_header_injection(self):
        """Тест Host Header Injection"""
        self.log_attack("HOST_HEADER", "Проверка ALLOWED_HOSTS=['*']")
        
        malicious_hosts = [
            "evil.com",
            "localhost.evil.com",
            "attackers-domain.com"
        ]
        
        for host in malicious_hosts:
            try:
                response = self.session.get(
                    f"{self.base_url}/",
                    headers={'Host': host}
                )
                
                # Если ответ успешный с поддельным хостом
                if response.status_code == 200:
                    print(f"❌ VULNERABLE: Host header accepts {host}")
                    return True
                    
            except Exception:
                pass
                
        print("✅ Host header защищен")
        return False
        
    def test_csrf_bypass(self):
        """Тест CSRF защиты"""
        self.log_attack("CSRF", "Проверка CSRF защиты")
        
        try:
            # Пробуем POST без CSRF токена
            response = self.session.post(f"{self.base_url}/accounts/login/", data={
                'username': 'test',
                'password': 'test'
            })
            
            # Если нет CSRF ошибки или редиректа
            if "CSRF token" not in response.text and response.status_code != 403:
                print("❌ VULNERABLE: CSRF защита отсутствует или ослаблена")
                return True
                
        except Exception:
            pass
            
        print("✅ CSRF защита работает")
        return False
        
    def test_api_endpoints(self):
        """Тест API endpoint безопасности"""
        self.log_attack("API_SECURITY", "Проверка API endpoints")
        
        api_endpoints = [
            "/api/v1/users/",
            "/api/v1/profile/",
            "/api/v1/auth/token/"
        ]
        
        vulnerabilities = []
        
        for endpoint in api_endpoints:
            try:
                # Тест без аутентификации
                response = self.session.get(f"{self.base_url}{endpoint}")
                
                if response.status_code == 200:
                    print(f"❌ {endpoint}: Доступ без аутентификации")
                    vulnerabilities.append(endpoint)
                    
                # Тест rate limiting
                for i in range(10):
                    response = self.session.get(f"{self.base_url}{endpoint}")
                    time.sleep(0.1)
                    
                if response.status_code != 429:
                    print(f"⚠️  {endpoint}: Нет rate limiting")
                    
            except Exception:
                pass
                
        if not vulnerabilities:
            print("✅ API endpoints защищены")
            
        return len(vulnerabilities) > 0
        
    def test_session_security(self):
        """Тест безопасности сессий"""
        self.log_attack("SESSION_SECURITY", "Проверка session cookies")
        
        try:
            response = self.session.get(f"{self.base_url}/")
            
            # Проверяем cookie security
            cookies = response.cookies
            
            issues = []
            
            for cookie in cookies:
                if 'sessionid' in cookie.name or 'csrftoken' in cookie.name:
                    if not cookie.secure:
                        issues.append(f"Cookie {cookie.name} не Secure")
                    if not cookie.has_nonstandard_attr('HttpOnly'):
                        issues.append(f"Cookie {cookie.name} не HttpOnly")
                    if 'SameSite' not in str(cookie):
                        issues.append(f"Cookie {cookie.name} без SameSite")
                        
            if issues:
                print("❌ Session security issues:")
                for issue in issues:
                    print(f"   - {issue}")
                return True
                
        except Exception:
            pass
            
        print("✅ Session cookies защищены")
        return False
        
    def test_information_leakage(self):
        """Тест на утечку информации в headers"""
        self.log_attack("INFO_LEAK", "Проверка HTTP headers")
        
        try:
            response = self.session.get(f"{self.base_url}/")
            headers = response.headers
            
            issues = []
            
            # Проверка на опасные заголовки
            if 'Server' in headers:
                issues.append(f"Server header: {headers['Server']}")
                
            if 'X-Powered-By' in headers:
                issues.append(f"X-Powered-By: {headers['X-Powered-By']}")
                
            # Проверка security headers
            security_headers = [
                'X-Content-Type-Options',
                'X-Frame-Options',
                'X-XSS-Protection',
                'Strict-Transport-Security'
            ]
            
            missing_headers = [h for h in security_headers if h not in headers]
            if missing_headers:
                issues.append(f"Missing security headers: {missing_headers}")
                
            if issues:
                print("❌ Information leakage:")
                for issue in issues:
                    print(f"   - {issue}")
                return True
                
        except Exception:
            pass
            
        print("✅ HTTP headers безопасны")
        return False
        
    def run_full_audit(self):
        """Полный аудит безопасности"""
        print("🚨 НАЧАЛО АУДИТА БЕЗОПАСНОСТИ")
        print("=" * 50)
        
        results = {
            'info_disclosure': self.test_information_disclosure(),
            'default_admin': self.test_default_admin_url(),
            'brute_force': self.test_brute_force_login(),
            'host_header': self.test_host_header_injection(),
            'csrf': self.test_csrf_bypass(),
            'api_security': self.test_api_endpoints(),
            'session_security': self.test_session_security(),
            'info_leakage': self.test_information_leakage()
        }
        
        print("\n" + "=" * 50)
        print("📊 РЕЗУЛЬТАТЫ АУДИТА")
        print("=" * 50)
        
        critical_issues = []
        warnings = []
        
        for test, vulnerable in results.items():
            status = "❌ VULNERABLE" if vulnerable else "✅ SECURE"
            print(f"{test.replace('_', ' ').title()}: {status}")
            
            if vulnerable:
                if test in ['brute_force', 'info_disclosure', 'host_header']:
                    critical_issues.append(test)
                else:
                    warnings.append(test)
                    
        print(f"\n🚨 Critical Issues: {len(critical_issues)}")
        for issue in critical_issues:
            print(f"   - {issue}")
            
        print(f"\n⚠️  Warnings: {len(warnings)}")
        for warning in warnings:
            print(f"   - {warning}")
            
        total_score = sum(1 for v in results.values() if not v)
        print(f"\n📊 Security Score: {total_score}/8 ({total_score/8*100:.1f}%)")
        
        if critical_issues:
            print("\n🔥 НЕМЕДЛЕННО ИСПРАВИТЬ КРИТИЧЕСКИЕ УЯЗВИМОСТИ!")
            
        return results

def main():
    """Главная функция"""
    print("🚨 Django CRM LMS Security Audit")
    print("📚 Educational Purpose Only - DO NOT USE FOR MALICIOUS ACTIVITIES")
    print("\n")
    
    simulator = AttackSimulator()
    
    try:
        results = simulator.run_full_audit()
        
        print("\n" + "=" * 50)
        print("📋 РЕКОМЕНДАЦИИ")
        print("=" * 50)
        
        if results['brute_force']:
            print("🔐 Усилите аутентификацию:")
            print("   - Включите 2FA")
            print("   - Усложните пароли")
            print("   - Настройте account lockout")
            
        if results['info_disclosure']:
            print("🔒 Скрыть информацию:")
            print("   - DEBUG=False в production")
            print("   - Настройте error pages")
            print("   - Удалите stack traces")
            
        if results['host_header']:
            print("🌐 Защитите network:")
            print("   - Ограничьте ALLOWED_HOSTS")
            print("   - Настройте HTTPS")
            print("   - Включите HSTS")
            
        if results['csrf']:
            print("🛡️ Усилите CSRF:")
            print("   - Удалите DevCsrfMiddleware")
            print("   - Включите CSRF protection")
            print("   - Настройте SameSite cookies")
            
    except KeyboardInterrupt:
        print("\n🛑 Аудит прерван")
    except Exception as e:
        print(f"\n❌ Ошибка аудита: {e}")

if __name__ == "__main__":
    main()
