import requests
import json
import re
from django.conf import settings

def grade_assignment_with_ai(assignment, student_submission):
    """
    Автоматическая проверка задания с помощью Gemini AI
    """
    api_key = "AIzaSyBeZR0odlretrnDQx481s0jtvNiufIDREo"
    
    # Проверяем, есть ли что оценивать
    if not student_submission.answer_text and not student_submission.file:
        return {
            'success': False,
            'error': 'Нет текста ответа или файла для оценки',
            'raw_response': None
        }
    
    # Формируем промпт для Gemini
    prompt = f"""
Ты - опытный преподаватель. Проанализируй задание и ответ студента, выстави оценку и напиши конструктивный комментарий.

ЗАДАНИЕ:
Название: {assignment.title}
Описание: {assignment.description}
Максимальный балл: {assignment.max_score}

ОТВЕТ СТУДЕНТА:
{student_submission.answer_text}

ФАЙЛЫ: {student_submission.file.url if student_submission.file else 'Нет файлов'}

Проанализируй ответ и верни JSON:
{{
    "score": 0-{assignment.max_score},
    "max_score": {assignment.max_score},
    "percentage": 0-100,
    "grade_level": "отлично/хорошо/удовлетворительно/неудовлетворительно",
    "strengths": ["сильная сторона 1", "сильная сторона 2"],
    "weaknesses": ["слабая сторона 1", "слабая сторона 2"],
    "detailed_feedback": "детальный комментарий студенту",
    "mentor_notes": "заметки для ментора",
    "suggestions": ["рекомендация 1", "рекомендация 2"],
    "plagiarism_check": {{
        "suspicious": false,
        "reason": "причина подозрения"
    }},
    "confidence": 0-100
}}

Критерии оценки:
- Полнота ответа (30%)
- Правильность (40%) 
- Структура и логика (20%)
- Оригинальность (10%)

Будь объективным, но справедливым. Дай конструктивную обратную связь.
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
        response = requests.post(url, headers=headers, json=data, timeout=30)
        response.raise_for_status()
        
        result = response.json()
        
        # Извлекаем текст ответа
        if 'candidates' in result and len(result['candidates']) > 0:
            content = result['candidates'][0]['content']['parts'][0]['text']
            
            # Ищем JSON в тексте
            start = content.find('{')
            end = content.rfind('}') + 1
            json_str = content[start:end]
            
            try:
                ai_result = json.loads(json_str)
                
                # Валидация и корректировка результатов
                ai_result['score'] = max(0, min(assignment.max_score, ai_result.get('score', 0)))
                ai_result['percentage'] = (ai_result['score'] / assignment.max_score) * 100
                
                return {
                    'success': True,
                    'ai_result': ai_result,
                    'raw_response': content
                }
                
            except json.JSONDecodeError as e:
                return {
                    'success': False,
                    'error': f'JSON parsing error: {e}',
                    'raw_response': content
                }
        else:
            return {
                'success': False,
                'error': f'Invalid API response: {result}',
                'raw_response': str(result)
            }
        
    except requests.RequestException as e:
        return {
            'success': False,
            'error': f'API request failed: {e}',
            'raw_response': None
        }
    except Exception as e:
        return {
            'success': False,
            'error': f'Unexpected error: {e}',
            'raw_response': None
        }

def batch_grade_assignments(assignments_submissions):
    """
    Массовая проверка заданий
    """
    results = []
    
    for submission in assignments_submissions:
        if submission.status == 'submitted' and not submission.grade:
            result = grade_assignment_with_ai(submission.assignment, submission)
            
            if result['success']:
                # Применяем оценку
                ai_result = result['ai_result']
                submission.grade = ai_result['score']
                submission.status = 'graded'
                submission.ai_graded = True
                submission.ai_feedback = ai_result
                submission.save()
                
                results.append({
                    'submission': submission,
                    'grade': ai_result['score'],
                    'percentage': ai_result['percentage'],
                    'feedback': ai_result['detailed_feedback']
                })
            else:
                results.append({
                    'submission': submission,
                    'error': result['error']
                })
    
    return results

def check_plagiarism(text):
    """
    Базовая проверка на плагиат
    """
    # Простые эвристики для обнаружения плагиата
    suspicious_patterns = [
        r'\b(copy|copied|from|source|reference)\b',
        r'\b(wikipedia|google|internet)\b',
        r'\b(https?://|www\.)\S+',
        r'\b\s{10,}\b',  # Много пробелов подряд
    ]
    
    suspicion_score = 0
    reasons = []
    
    for pattern in suspicious_patterns:
        matches = re.findall(pattern, text.lower())
        if matches:
            suspicion_score += len(matches) * 10
            reasons.append(f"Found pattern: {pattern}")
    
    # Проверка на повторяющиеся предложения
    sentences = text.split('.')
    repeated_sentences = len(sentences) - len(set(sentences))
    if repeated_sentences > 2:
        suspicion_score += repeated_sentences * 5
        reasons.append("Repetitive sentences detected")
    
    return {
        'suspicious': suspicion_score > 30,
        'score': suspicion_score,
        'reasons': reasons
    }
