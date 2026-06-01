from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse
from django.contrib import messages
from django.db.utils import IntegrityError
from django.contrib.auth.decorators import login_required
from .models import Request, Response, CustomUser
from .forms import ResponseForm, RequestForm, CustomerRegistrationForm, CarrierRegistrationForm

# Create your views here.

def create_request(request):
    if request.method == 'POST':
        form = RequestForm(request.POST)
        if form.is_valid():
            # Указываем текущего пользователя в поле created_by
            new_request = form.save(commit=False)
            new_request.created_by = request.user
            new_request.save()
            return redirect('request_list')
    else:
        form = RequestForm()
    return render(request, 'create_request.html', {'form': form})

def create_response(request, request_id):
    request_obj = get_object_or_404(Request, id=request_id)  # Находим заявку по ID
    if request.method == "POST":
        form = ResponseForm(request.POST)
        if form.is_valid():
            response = form.save(commit=False)
            response.request = request_obj  # Привязываем отклик к заявке
            response.carrier = request.user  # Привязываем отклик к текущему перевозчику
            response.save()
            return redirect('request_detail', request_id=request_obj.id)  # Перенаправляем на страницу заявки
    else:
        form = ResponseForm()
    
    return render(request, 'create_response.html', {'form': form, 'request': request_obj})

def request_detail(request, request_id):
    request_obj = get_object_or_404(Request, id=request_id)
    responses = request_obj.responses.all()
    existing_response = None

    if request.user.is_authenticated and request.user.role == 'CARRIER':
        existing_response = Response.objects.filter(request=request_obj, carrier=request.user).first()

    # Инициализация формы (по умолчанию для GET-запросов)
    form = ResponseForm(initial={'price': existing_response.price if existing_response else None})

    if request.method == "POST":
        form = ResponseForm(request.POST)
        if form.is_valid():
            try:
                response, created = Response.objects.get_or_create(
                    request=request_obj,
                    carrier=request.user,
                    defaults={
                        'price': form.cleaned_data['price'],
                        'message': form.cleaned_data.get('message', ''),
                    }
                )
                if not created:
                    # Обновите существующий отклик, если он уже есть
                    response.price = form.cleaned_data['price']
                    response.message = form.cleaned_data.get('message', response.message)
                    response.save()
                return redirect('request_detail', request_id=request_obj.id)
            except IntegrityError:
                form.add_error(None, "Ошибка: вы уже откликнулись на эту заявку.")

    return render(request, 'request_detail.html', {
        'request': request_obj,
        'form': form,
        'responses': responses,
        'existing_response': existing_response,
    })
    
    # Фильтрация откликов по пользователю
    if request.user == request_obj.created_by:
        responses = request_obj.responses.all()  # Получаем все отклики для заявки

    return render(request, 'request_detail.html', {'request': request_obj, 'form': form, 'responses': responses})

def request_list(request):
    # Извлекаем все заявки
    requests = Request.objects.all()  # Можно использовать фильтрацию или сортировку по дате, если нужно
    return render(request, 'request_list.html', {'requests': requests})

def home(request):
    # Получаем последние 5 заявок, сортируя по дате создания (по убыванию)
    latest_requests = Request.objects.all().order_by('-created_at')[:5]
    return render(request, 'home.html', {'latest_requests': latest_requests})

def register_customer(request):
    if request.method == 'POST':
        form = CustomerRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)  # Сохраняем объект, не сохраняя в базу
            generated_password = user.set_random_password()  # Генерируем пароль
            user.set_password(generated_password)  # Устанавливаем хэшированный пароль
            user.save()  # Сохраняем пользователя с новым паролем
            return render(request, 'success.html', {'form': form})
            # messages.success(request, "Пользователь успешно зарегистрирован.")    
    else:
        form = CustomerRegistrationForm()
    return render(request, 'register_customer.html', {'form': form})

@login_required
def user_orders(request):
    user_orders = Request.objects.filter(created_by=request.user)  # Заказы текущего пользователя
    return render(request, 'user_orders.html', {'orders': user_orders})

def register_carrier(request):
    if request.method == 'POST':
        form = CarrierRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)  # Не сохраняем еще пользователя
            generated_password = user.set_random_password()  # Генерируем пароль
            user.set_password(generated_password)  # Устанавливаем хэшированный пароль
            user.role = CustomUser.Roles.CARRIER  # Присвоить роль
            user.save()  # Сохраняем пользователя с новым паролем
            messages.success(request, "Перевозчик успешно зарегистрирован.")
            return render(request, 'success.html', {'form': form})
    else:
        form = CarrierRegistrationForm()

    return render(request, 'register_carrier.html', {'form': form})

def accept_response(request, response_id):
    response = get_object_or_404(Response, id=response_id)
    if request.user == response.request.created_by:
        response.is_accepted = True
        response.save()
    return redirect('request_detail', request_id=response.request.id)

@login_required
def carrier_dashboard(request):
    if request.user.role != 'carrier':
        return redirect('user_orders')  # Перенаправляем не перевозчиков на главную

    # Отклики текущего перевозчика
    responses = Response.objects.filter(carrier=request.user)

    # Последние 10 заказов
    latest_requests = Request.objects.order_by('-created_at')[:10]

    return render(request, 'carrier_dashboard.html', {
        'responses': responses,
        'latest_requests': latest_requests,
    })