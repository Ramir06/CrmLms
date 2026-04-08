import requests
import base64
import json
import logging
from typing import Dict, List, Optional, Union
from django.conf import settings
from django.core.files.base import ContentFile

logger = logging.getLogger(__name__)


class NVIDIAAIService:
    """Сервис для работы с NVIDIA AI API"""
    
    def __init__(self):
        self.api_key = getattr(settings, 'NVIDIA_API_KEY', '')
        self.invoke_url = "https://integrate.api.nvidia.com/v1/chat/completions"
        self.model = "qwen/qwen3.5-397b-a17b"
        self.max_tokens = 16384
        self.temperature = 0.60
        self.top_p = 0.95
        self.top_k = 20
        self.presence_penalty = 0
        self.repetition_penalty = 1
        
        if not self.api_key:
            logger.warning("NVIDIA_API_KEY не настроен в настройках")
    
    def _make_request(self, messages: List[Dict], stream: bool = False) -> Union[str, Dict]:
        """Выполняет запрос к NVIDIA AI API"""
        if not self.api_key:
            return {"error": "API ключ не настроен"}
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "text/event-stream" if stream else "application/json"
        }
        
        payload = {
            "model": self.model,
            "messages": messages,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "top_p": self.top_p,
            "top_k": self.top_k,
            "presence_penalty": self.presence_penalty,
            "repetition_penalty": self.repetition_penalty,
            "stream": stream,
            "chat_template_kwargs": {"enable_thinking": True},
        }
        
        try:
            response = requests.post(self.invoke_url, headers=headers, json=payload, stream=stream, timeout=30)
            
            if stream:
                result = ""
                for line in response.iter_lines():
                    if line:
                        decoded_line = line.decode("utf-8")
                        if decoded_line.startswith("data: "):
                            data = decoded_line[6:]
                            if data != "[DONE]":
                                try:
                                    json_data = json.loads(data)
                                    if "choices" in json_data and len(json_data["choices"]) > 0:
                                        delta = json_data["choices"][0].get("delta", {})
                                        if "content" in delta:
                                            result += delta["content"]
                                except json.JSONDecodeError:
                                    continue
                return result
            else:
                if response.status_code == 200:
                    return response.json()
                else:
                    logger.error(f"API Error: {response.status_code} - {response.text}")
                    return {"error": f"API Error: {response.status_code}"}
                    
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error: {str(e)}")
            return {"error": f"Request error: {str(e)}"}
    
    def read_base64(self, file_path: str) -> str:
        """Читает файл и возвращает base64 строку"""
        try:
            with open(file_path, "rb") as f:
                return base64.b64encode(f.read()).decode()
        except Exception as e:
            logger.error(f"Error reading file {file_path}: {str(e)}")
            return ""
    
    def check_assignment(self, assignment_text: str, student_answer: str, criteria: str = "") -> Dict:
        """Проверяет задание с помощью AI"""
        messages = [
            {
                "role": "system",
                "content": """Ты - опытный преподаватель, который проверяет студенческие работы.
                Твоя задача:
                1. Оценить ответ студента по шкале от 1 до 10
                2. Дать подробную обратную связь
                3. Указать сильные стороны и ошибки
                4. Рекомендовать, как улучшить ответ
                
                Формат ответа (JSON):
                {
                    "score": 8,
                    "feedback": "Подробная обратная связь",
                    "strengths": ["сильная сторона 1", "сильная сторона 2"],
                    "weaknesses": ["ошибка 1", "ошибка 2"],
                    "recommendations": ["рекомендация 1", "рекомендация 2"],
                    "summary": "Краткое резюме"
                }"""
            },
            {
                "role": "user",
                "content": f"""Задание: {assignment_text}
                
                Критерии оценки: {criteria if criteria else "Общая оценка понимания темы"}
                
                Ответ студента:
                {student_answer}
                
                Проверь работу и верни результат в формате JSON."""
            }
        ]
        
        result = self._make_request(messages)
        
        if isinstance(result, dict) and "error" in result:
            return result
        
        try:
            # Если результат - строка (stream), пытаемся извлечь JSON
            if isinstance(result, str):
                # Ищем JSON в строке
                start = result.find("{")
                end = result.rfind("}") + 1
                if start != -1 and end > start:
                    json_str = result[start:end]
                    return json.loads(json_str)
                else:
                    return {"error": "Не удалось извлечь JSON из ответа AI", "raw_response": result}
            
            # Если результат - словарь (не stream)
            if isinstance(result, dict) and "choices" in result:
                content = result["choices"][0]["message"]["content"]
                start = content.find("{")
                end = content.rfind("}") + 1
                if start != -1 and end > start:
                    json_str = content[start:end]
                    return json.loads(json_str)
            
            return {"error": "Неожиданный формат ответа", "raw_response": result}
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {str(e)}")
            return {"error": f"Ошибка парсинга JSON: {str(e)}", "raw_response": result}
    
    def analyze_dashboard(self, dashboard_data: Dict) -> Dict:
        """Анализирует данные дашборда и дает рекомендации"""
        messages = [
            {
                "role": "system",
                "content": """Ты - бизнес-аналитик, который анализирует данные CRM LMS системы.
                Твоя задача:
                1. Проанализировать показатели дашборда
                2. Выявить тренды и аномалии
                3. Дать рекомендации по улучшению
                4. Предсказать возможные проблемы
                
                Формат ответа (JSON):
                {
                    "overview": "Общий анализ ситуации",
                    "key_insights": ["инсайт 1", "инсайт 2"],
                    "trends": ["тренд 1", "тренд 2"],
                    "warnings": ["предупреждение 1", "предупреждение 2"],
                    "recommendations": ["рекомендация 1", "рекомендация 2"],
                    "predictions": ["прогноз 1", "прогноз 2"]
                }"""
            },
            {
                "role": "user",
                "content": f"""Данные дашборда CRM LMS:
                {json.dumps(dashboard_data, ensure_ascii=False, indent=2)}
                
                Проанализируй эти данные и верни результат в формате JSON."""
            }
        ]
        
        result = self._make_request(messages)
        
        if isinstance(result, dict) and "error" in result:
            return result
        
        try:
            # Если результат - строка (stream), пытаемся извлечь JSON
            if isinstance(result, str):
                start = result.find("{")
                end = result.rfind("}") + 1
                if start != -1 and end > start:
                    json_str = result[start:end]
                    return json.loads(json_str)
                else:
                    return {"error": "Не удалось извлечь JSON из ответа AI", "raw_response": result}
            
            # Если результат - словарь (не stream)
            if isinstance(result, dict) and "choices" in result:
                content = result["choices"][0]["message"]["content"]
                start = content.find("{")
                end = content.rfind("}") + 1
                if start != -1 and end > start:
                    json_str = content[start:end]
                    return json.loads(json_str)
            
            return {"error": "Неожиданный формат ответа", "raw_response": result}
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {str(e)}")
            return {"error": f"Ошибка парсинга JSON: {str(e)}", "raw_response": result}
    
    def generate_summary(self, text: str, max_length: int = 200) -> str:
        """Генерирует краткое изложение текста"""
        messages = [
            {
                "role": "system",
                "content": f"""Ты - ассистент, который создает краткие изложения текстов.
                Сократи текст до {max_length} символов, сохранив основную суть."""
            },
            {
                "role": "user",
                "content": f"Текст для изложения:\n{text}"
            }
        ]
        
        result = self._make_request(messages)
        
        if isinstance(result, dict):
            if "error" in result:
                return f"Ошибка: {result['error']}"
            elif "choices" in result:
                return result["choices"][0]["message"]["content"]
        
        return str(result) if result else "Не удалось сгенерировать изложение"
    
    def translate_text(self, text: str, target_language: str = "ru") -> str:
        """Переводит текст на указанный язык"""
        messages = [
            {
                "role": "system",
                "content": f"Ты - профессиональный переводчик. Переведи текст на {target_language} язык."
            },
            {
                "role": "user",
                "content": f"Текст для перевода:\n{text}"
            }
        ]
        
        result = self._make_request(messages)
        
        if isinstance(result, dict):
            if "error" in result:
                return f"Ошибка: {result['error']}"
            elif "choices" in result:
                return result["choices"][0]["message"]["content"]
        
        return str(result) if result else "Не удалось перевести текст"
    
    def analyze_student_progress(self, student_data: Dict) -> Dict:
        """Анализирует прогресс студента"""
        messages = [
            {
                "role": "system",
                "content": """Ты - опытный преподаватель, который анализирует прогресс студента.
                Проанализируй данные студента и дай рекомендации по улучшению обучения.
                
                Формат ответа (JSON):
                {
                    "overall_progress": "Общая оценка прогресса",
                    "strengths": ["сильная сторона 1", "сильная сторона 2"],
                    "areas_for_improvement": ["область для улучшения 1", "область для улучшения 2"],
                    "recommendations": ["рекомендация 1", "рекомендация 2"],
                    "next_steps": ["следующий шаг 1", "следующий шаг 2"],
                    "risk_factors": ["фактор риска 1", "фактор риска 2"]
                }"""
            },
            {
                "role": "user",
                "content": f"""Данные студента:
                {json.dumps(student_data, ensure_ascii=False, indent=2)}
                
                Проанализируй прогресс студента и верни результат в формате JSON."""
            }
        ]
        
        result = self._make_request(messages)
        
        if isinstance(result, dict) and "error" in result:
            return result
        
        try:
            if isinstance(result, str):
                start = result.find("{")
                end = result.rfind("}") + 1
                if start != -1 and end > start:
                    json_str = result[start:end]
                    return json.loads(json_str)
                else:
                    return {"error": "Не удалось извлечь JSON из ответа AI", "raw_response": result}
            
            if isinstance(result, dict) and "choices" in result:
                content = result["choices"][0]["message"]["content"]
                start = content.find("{")
                end = content.rfind("}") + 1
                if start != -1 and end > start:
                    json_str = content[start:end]
                    return json.loads(json_str)
            
            return {"error": "Неожиданный формат ответа", "raw_response": result}
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {str(e)}")
            return {"error": f"Ошибка парсинга JSON: {str(e)}", "raw_response": result}


# Глобальный экземпляр сервиса
nvidia_ai_service = NVIDIAAIService()
