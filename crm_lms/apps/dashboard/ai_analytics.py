import requests
import json
from django.conf import settings

def get_gemini_analysis(student_data):
    """
    Отправляет данные студента в Gemini API для анализа
    """
    api_key = "AIzaSyBeZR0odlretrnDQx481s0jtvNiufIDREo"
    
    # Формируем промпт для Gemini
    prompt = f"""
Проанализируй данные студента и дай прогноз:

Студент: {student_data['student_name']}
Курс: {student_data['course_title']}
Средний балл: {student_data['recent_avg']}%
Тренд успеваемости: {student_data['grade_trend']}%
Посещаемость: {student_data['attendance_rate']}%
Количество пропусков: {student_data['absent_count']}
Неуспешных заданий: {student_data['failed_count']}

Дай краткий анализ в формате JSON:
{{
    "risk_level": "низкий/средний/высокий",
    "prediction": "уйдет с курса/останется/улучшится",
    "confidence": 0-100,
    "main_factors": ["фактор1", "фактор2"],
    "recommendations": ["рекомендация1", "рекомендация2"],
    "summary": "краткое резюме на русском языке"
}}
"""
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={api_key}"
    
    headers = {
        'Content-Type': 'application/json',
    }
    
    data = {
        "contents": [{
            "parts": [{
                "text": prompt
            }]
        }]
    }
    
    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        
        result = response.json()
        
        # Извлекаем текст ответа
        if 'candidates' in result and len(result['candidates']) > 0:
            content = result['candidates'][0]['content']['parts'][0]['text']
            
            # Пытаемся распарсить JSON из ответа
            try:
                # Ищем JSON в тексте
                start = content.find('{')
                end = content.rfind('}') + 1
                json_str = content[start:end]
                
                return json.loads(json_str)
            except json.JSONDecodeError:
                # Если не удалось распарсить JSON, возвращаем базовый анализ
                return {
                    "risk_level": "средний",
                    "prediction": "останется",
                    "confidence": 70,
                    "main_factors": ["недостаточно данных"],
                    "recommendations": ["требуется дополнительный анализ"],
                    "summary": content[:200] + "..." if len(content) > 200 else content
                }
        
        return None
        
    except requests.RequestException as e:
        print(f"Error calling Gemini API: {e}")
        return None

def analyze_student_with_ai(student_data):
    """
    Анализирует студента с использованием Gemini API
    """
    ai_result = get_gemini_analysis(student_data)
    
    if ai_result:
        return {
            **student_data,
            'ai_analysis': ai_result
        }
    else:
        # Fallback к базовому анализу если API недоступен
        return {
            **student_data,
            'ai_analysis': {
                "risk_level": "неизвестно",
                "prediction": "требуется анализ",
                "confidence": 0,
                "main_factors": ["API недоступен"],
                "recommendations": ["повторите попытку позже"],
                "summary": "Не удалось получить AI-анализ"
            }
        }
