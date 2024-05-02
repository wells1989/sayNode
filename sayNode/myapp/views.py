from django.shortcuts import render, HttpResponse
import json
from django.http import JsonResponse
from django.middleware.csrf import get_token
from django.views.decorators.csrf import csrf_exempt, ensure_csrf_cookie

# version with csrf_exempt
@csrf_exempt 
def sum_integers(request):

    try:

        data = json.loads(request.body)

        int_1 = int(data.get("int_1"))
        int_2 = int(data.get("int_2"))

        total = int_1 + int_2

        return JsonResponse({'sum': total})
    
    except (TypeError, ValueError):
        return JsonResponse({'error': 'Please provide valid integers for num1 and num2'}, status=400)
    
