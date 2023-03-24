# Create your views here.
from django.shortcuts import get_object_or_404, render,redirect
from django.contrib import messages, auth
from django.contrib.auth import login, authenticate
from django.contrib.admin.views.decorators import staff_member_required
from category.models import Category, Sub_Category
from shop.models import ContactMessage
from django.contrib import messages
from datetime import datetime,timedelta
from accounts.models import *
from orders.models import *
import calendar
from django.db.models import Q
from django.db.models import Sum
from django.views.decorators.cache import never_cache
from .forms import loginForm, productForm, categoryForm, subCategoryForm, userForm, couponForm
from django.core.mail import EmailMessage
from django.core.paginator import Paginator
from django.utils import timezone


@never_cache
def adminLogin(request):
  if 'email' in request.session:
    return redirect('adminDashboard')
    
  if request.method == 'POST':
    form = loginForm(request.POST)
    email = request.POST['email']
    password = request.POST['password']
    
    user = authenticate(email=email, password=password)
    
    if user is not None:
      if user.is_superadmin:
        request.session['email'] = email
        
        login(request, user)
        return redirect('adminDashboard')
        
      else:
        messages.error(request, 'You are not autherized to access admin panel')
        return redirect('adminLogin')
    else:
      messages.error(request, 'Invalid login credentials')
      return redirect('adminLogin')
    
  form = loginForm
  return render(request, 'adminPanel/adminLogin.html', {'form':form})
  

@staff_member_required(login_url='adminLogin')
def adminLogout(request):
    if 'email' in request.session:
        request.session.flush()
    auth.logout(request)
    messages.success(request, "You are logged out.")
    return redirect('adminLogin')


@staff_member_required(login_url = 'adminLogin')
def adminDashboard(request):
    customers_count = Account.objects.filter(is_admin=False).count()
    orders_count = Order.objects.filter(is_ordered=True).count()
    product_count = Product.objects.filter(is_available=True).count()
    total_orders = Order.objects.filter(is_ordered=True).order_by('created_at')
    first_order_date = total_orders[0].created_at.date()
    total_sales = round(sum(list(map(lambda x : x.order_total,total_orders))),2)
    today = datetime.today()
    this_year = today.year
    this_month = today.month
    label_list = []
    line_data_list = []
    bar_data_list =  []
    month_list=[]
    for year in range(first_order_date.year,this_year+1) :
        month = this_month if year==this_year else 12
        month_list= month_list+(list(map(lambda x : calendar.month_abbr[x]+'-'+str(year),range(1,month+1))))[::-1]
    for year in range(2022,(this_year+1)):
        this_month = this_month if year==this_year else 12
        for month in range(1,(this_month+1)):
            month_wise_total_orders = Order.objects.filter(is_ordered=True,created_at__year = year,created_at__month=month,).order_by('created_at').count()
            month_name = calendar.month_abbr[month]
            label_update = str(month_name)+ ' ' + str(year)
            label_list.append(label_update)
            line_data_list.append(month_wise_total_orders)
    for year in range(2022,(this_year+1)):
        for month in range(1,(this_month+1)):
            monthwise_orders = Order.objects.filter(is_ordered=True,created_at__year = year,created_at__month=month,)
            monthwise_sales  = round(sum(list(map(lambda x : x.order_total,monthwise_orders))),2)
            bar_data_list.append(monthwise_sales)
     
    context = {
        'total_customers' : customers_count,
        'total_orders'    : orders_count,
        'total_products'  : product_count,
        'total_sales'     : total_sales,
        'month_list'      : month_list,
        'line_labels'     : label_list,
        'line_data'       : line_data_list,
        'bar_data'        : bar_data_list
    }
    return render(request,'adminPanel/adminDashboard.html',context)


@staff_member_required(login_url = 'adminLogin')
def adminDashboardMonthwise(request,month):
    total_orders = Order.objects.filter(is_ordered=True).order_by('created_at')
    first_order_date = total_orders[0].created_at.date()
    taken_month = month
    selected_month = taken_month[:3]
    selected_year = taken_month[4:9]
    today = datetime.today()
    selected_month_num = datetime.strptime(selected_month, '%b').month
    month_range  =calendar.monthrange(int(selected_year),int(selected_month_num))[1]
    
    day = today.day if selected_year==today.year else month_range
    month = datetime.strptime(selected_month, '%b').month
    customers_count = Account.objects.filter(is_admin=False,date_jointed__year= selected_year,date_jointed__month=month).count()
    orders_count = Order.objects.filter(is_ordered=True,created_at__year = selected_year,created_at__month=month,).count()
    product_count = Product.objects.filter(is_available=True,created_date__year=selected_year,created_date__month=month).count()
    total_orders = Order.objects.filter(is_ordered=True,created_at__year = selected_year,created_at__month=month,).order_by('created_at')
    
    total_sales = round(sum(list(map(lambda x : x.order_total,total_orders))),2)
    month_list=[]
    for year in range(first_order_date.year,today.year+1) :
        month = today.month if year==today.year else 12
        month_list= month_list+(list(map(lambda x : calendar.month_abbr[x]+'-'+str(year),range(1,month+1))))[::-1]
    # x= total_orders[0].created_at.date().day
    order_count_per_day = []
    for day in range (1,(day+1)):
        day_order = Order.objects.filter(is_ordered=True,created_at__year = selected_year,created_at__month=selected_month_num, created_at__day=day).count()
        order_count_per_day.append(day_order)
    days = list(range(1,day+1))
    sales_per_day =[]
    for day in range (1,(day+1)):
        day_order = Order.objects.filter(is_ordered=True,created_at__year = selected_year,created_at__month=selected_month_num, created_at__day=day)
        day_sales = sum(list(map(lambda x : x.order_total,day_order)))
        sales_per_day.append(day_sales)

    context = {
        'total_customers' : customers_count,
        'total_orders'    : orders_count,
        'total_products'  : product_count,
        'total_sales'     : total_sales,
        'month_list'      : month_list,
        'selected_month'  : taken_month,
        'line_labels'     : days,
        'line_data'       : order_count_per_day,
        'bar_data'        : sales_per_day,
    }
    
    return render(request,'adminPanel/adminDashboard.html',context)


@staff_member_required(login_url = 'adminLogin')
def adminMessages(request):
    messages_recieved  = ContactMessage.objects.all().order_by('-sent_time')
    context = {
        'messages_recieved' : messages_recieved,
    }
    return render(request,'adminPanel/adminMessages.html',context)


@staff_member_required(login_url = 'adminLogin')
def deleteMessage(request,id):
    message = ContactMessage.objects.get(id=id)
    message.delete()
    messages.error(request,'message deleted successfully!')
    return redirect('adminMessages')


@staff_member_required(login_url = 'adminLogin')
def replyMessage(request):
    try:
        if request.method == 'POST':
            email = request.POST['email']
            message = request.POST['message']
            mail_subject = ''' Reply from Fresh Harvest Ecommerce shop'''
            send_mail = EmailMessage(mail_subject,message,to=[email])
            send_mail.send()
            messages.success(request,'Message sent successfully')
        else:
            messages.error(request,'please fill the form correctly')
    except:
        messages.error(request,'Server down! please ensure you are connected to internet')
    return redirect('adminMessages')


# Admin User Management
@staff_member_required(login_url = 'adminLogin')
def adminUserManagement(request):
  if request.method == 'POST':
    search_key = request.POST.get('search')
    users = Account.objects.filter(Q(first_name__icontains=search_key) | Q(last_name__icontains=search_key) | Q(email__icontains=search_key),is_superadmin=False)
    paginator = Paginator(users, 5)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
  else:
    users = Account.objects.all().filter(is_superadmin=False).order_by('-id')
    paginator = Paginator(users, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
  context = {
    'users': page_obj
  }
  return render(request,'adminpanel/usermanagement/adminusermanagement.html',context)


@staff_member_required(login_url = 'adminLogin')
def editUserData(request, id):
  user = Account.objects.get(id=id)
  
  if request.method == 'POST':
    form = userForm(request.POST, request.FILES, instance=user)
    if form.is_valid():
      form.save()
      messages.success(request, 'User Account edited successfully.')
      return redirect('adminUserManagement')
    else:
      messages.error(request, 'Invalid input!!!')
      return redirect('editUserData', id)
    
  else:
    form = userForm(instance=user)
  
  context = {
    'form':form,
    'id':id,
  }
    
  return render(request, 'adminPanel/userManagement/editUserData.html', context)


@staff_member_required(login_url = 'adminLogin')
def blockUser(request, id):
    users = Account.objects.get(id=id)
    if users.is_active:
        users.is_active = False
        users.save()

    else:
         users.is_active = True
         users.save()

    return redirect('adminUserManagement')


# Admin Category Management
@staff_member_required(login_url = 'adminLogin')
def adminCategories(request):
  categories = Category.objects.all().order_by('id')
  
  paginator = Paginator(categories, 10)
  page_number = request.GET.get('page')
  page_obj = paginator.get_page(page_number)
  
  context = {
    'categories':page_obj
  }
  return render(request, 'adminPanel/categoryManagement/adminCategories.html', context)


@staff_member_required(login_url = 'adminLogin')
def adminAddCategory(request):
  if request.method == 'POST':
    form = categoryForm(request.POST, request.FILES)
    if form.is_valid():
      form.save()
      messages.success(request, 'Category added successfully.')
      return redirect('adminCategories')
    else:
      messages.error(request, 'Invalid input!!!')
      return redirect('adminAddCategory')
  else:
    form = categoryForm()
    context = {
      'form':form,
    }
    return render(request, 'adminPanel/categoryManagement/adminAddCategory.html', context)
  

@staff_member_required(login_url = 'adminLogin')
def adminEditCategory(request, category_slug):
  category = Category.objects.get(slug=category_slug)
  
  if request.method == 'POST':
    form = categoryForm(request.POST, request.FILES, instance=category)
    
    if form.is_valid():
      form.save()
      messages.success(request, 'Category edited successfully.')
      return redirect('adminCategories')
    else:
      messages.error(request, 'Invalid input')
      return redirect('adminEditCategory', category_slug)
      
  form =   categoryForm(instance=category)
  context = {
    'form':form,
    'category':category,
  }
  return render(request, 'adminPanel/categoryManagement/adminEditCategory.html', context)
  

@staff_member_required(login_url = 'adminLogin')  
def adminDeleteCategory(request, category_slug):
  category = Category.objects.get(slug=category_slug)
  category.delete()
  messages.success(request, 'Category deleted successfully.')
  return redirect('adminCategories')


#  Admin Category Offers
@staff_member_required(login_url = 'adminLogin')  
def categoryOffers(request):
  categories = Category.objects.all().order_by('-category_offer')
  
  paginator = Paginator(categories, 10)
  page_number = request.GET.get('page')
  page_obj = paginator.get_page(page_number)
  
  context = {
    'categories':page_obj,
  }
  return render(request, 'adminPanel/categoryManagement/adminCategoryOffers.html', context)


@staff_member_required(login_url= 'adminLogin')
def addCategoryOffer(request):
  if request.method == 'POST' :
    category_name = request.POST.get('category_name')
    category_offer = request.POST.get('category_offer')
    category = Category.objects.get(category_name = category_name)
    category.category_offer =  category_offer
    category.save()
    messages.success(request,'Category offer added successfully')
    return redirect('categoryOffers')
      

@staff_member_required(login_url= 'adminLogin')
def deleteCategoryOffer(request, id):
  category = Category.objects.get(id = id)
  category.category_offer =  0
  category.save()
  messages.success(request,'Category offer deleted successfully')
  return redirect('categoryOffers')


# Subcategory management
@staff_member_required(login_url = 'adminLogin')
def subCategories(request, category_slug):
  sub_categories = Sub_Category.objects.all().filter(category__slug=category_slug)
  context = {
    'sub_categories':sub_categories,
    'category_slug':category_slug,
  }
  return render(request, 'adminPanel/categoryManagement/adminSubcategories.html', context)


@staff_member_required(login_url = 'adminLogin')
def addSubcategory(request, category_slug):
  category = Category.objects.get(slug=category_slug)
  if request.method == 'POST':
    form = subCategoryForm(request.POST, request.FILES)
    if form.is_valid():
      form.save()
      messages.success(request, 'Subcategory added successfully.')
      return redirect('adminSubcategories', category_slug)
    else:
      messages.error(request, 'Invalid input!!!')
      return redirect('adminAddSubcategory', category_slug)
  else:
    form = subCategoryForm()
    context = {
      'form':form,
      'category':category
    }
    return render(request, 'adminPanel/categoryManagement/addSubcategory.html', context)
  

@staff_member_required(login_url = 'adminLogin')
def editSubcategory(request, slug):
  sub_category = Sub_Category.objects.get(slug=slug)
  cat_slug = sub_category.category.slug
  
  if request.method == 'POST':
    form = subCategoryForm(request.POST, request.FILES, instance=sub_category)
    
    if form.is_valid():
      form.save()
      messages.success(request, 'Subcategory edited successfully.')
      return redirect('adminSubcategories', cat_slug)
    else:
      messages.error(request, 'Invalid input')
      return redirect('editSubcategory')
      
  form =   subCategoryForm(instance=sub_category)
  context = {
    'form':form,
    'sub_category':sub_category,
  }
  return render(request, 'adminPanel/categoryManagement/adminEditSubcategory.html', context)


@staff_member_required(login_url = 'adminLogin')  
def deleteSubcategory(request, slug):
  sub_category = Sub_Category.objects.get(slug=slug)
  category_slug = sub_category.category.slug
  sub_category.delete()
  messages.success(request, 'Subcategory deleted successfully.')
  return redirect('adminSubcategories', category_slug)
 

# Product management
@staff_member_required(login_url = 'adminLogin')
def adminProducts(request):
  if request.method == 'POST':
    search_key = request.POST.get('search')
    products = Product.objects.filter(Q(product_name__icontains=search_key))
    paginator = Paginator(products, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
  else:
    products = Product.objects.all().order_by('-id')
    paginator = Paginator(products, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
  
  context = {
    'products': page_obj
  }
  return render(request, 'adminPanel/productManagement/adminProducts.html', context)


@staff_member_required(login_url = 'adminLogin')
def adminAddProduct(request):
  if request.method == 'POST':
    form = productForm(request.POST, request.FILES)
    if form.is_valid():
      form.save()
      messages.success(request, 'Product added successfully.')
      return redirect('adminProducts')
    else:
      messages.error(request, 'Invalid input!!!')
      return redirect('adminAddProduct')
  else:
    form = productForm()
    context = {
      'form':form,
    }
    return render(request, 'adminPanel/productManagement/adminAddProduct.html', context)


@staff_member_required(login_url = 'adminLogin')
def adminEditProduct(request, id):
  product = Product.objects.get(id=id)
  
  if request.method == 'POST':
    form = productForm(request.POST, request.FILES, instance=product)
    
    if form.is_valid():
      form.save()
      messages.success(request, 'product data edited successfully.')
      return redirect('adminProducts')
    else:
      messages.error(request, 'Invalid parameters')
      
  form =   productForm(instance=product)
  context = {
    'form':form,
    'product':product,
  }
  return render(request, 'adminPanel/productManagement/adminEditProduct.html', context)


@staff_member_required(login_url = 'adminLogin')  
def adminDeleteProduct(request, id):
  product = Product.objects.get(id=id)
  product.delete()
  return redirect('adminProducts')


@staff_member_required(login_url = 'adminLogin')  
def adminProductOffers(request):
  products = Product.objects.all().order_by('-product_offer')
  
  paginator = Paginator(products, 10)
  page_number = request.GET.get('page')
  page_obj = paginator.get_page(page_number)
  
  context = {
    'products':page_obj,
  }
  return render(request, 'adminPanel/productManagement/adminProductOffers.html', context)


@staff_member_required(login_url= 'adminLogin')
def addProductOffer(request):
  if request.method == 'POST' :
    product_name = request.POST.get('product_name')
    product_offer = request.POST.get('product_offer')
    product = Product.objects.get(product_name = product_name)
    product.product_offer =  product_offer
    product.save()
    messages.success(request,'Product offer added successfully')
    return redirect('adminProductOffers')
  

@staff_member_required(login_url= 'adminLogin')
def deleteProductOffer(request, id):
  product = Product.objects.get(id=id)
  product.product_offer = 0
  product.save()
  messages.success(request, 'Product offer deleted successfully')
  return redirect('adminProductOffers')

@staff_member_required(login_url = 'adminLogin')
def adminOrders(request):
  orders = Order.objects.filter(is_ordered=True).order_by('-id')
  paginator = Paginator(orders, 10)
  page_number = request.GET.get('page')
  page_obj = paginator.get_page(page_number)
  
  context = {
    'orders':page_obj,
  }
  return render(request, 'adminPanel/orderManagement/adminOrders.html', context)


@staff_member_required(login_url = 'adminLogin')
def adminChangeOrder(request, id):
  if request.method == 'POST':
    order = get_object_or_404(Order, id=id)
    status = request.POST.get('status')
    order.status = status 
    order.save()
    if status  == "Delivered":
      try:
          payment = Payment.objects.get(payment_id = order.order_number, status = False)
          if payment.payment_method == 'Cash On Delivery':
              payment.status = True
              payment.save()
      except:
          pass
  return redirect('adminOrders')


@staff_member_required(login_url = 'adminLogin')
def adminCoupons(request):
  coupons = Coupon.objects.all()
  context = {
    'coupons':coupons,
  }
  return render(request, 'adminPanel/couponManagement/adminCoupons.html', context)


@staff_member_required(login_url = 'adminLogin')
def adminAddCoupon(request):
  if request.method == 'POST':
    form = couponForm(request.POST , request.FILES)
    if form.is_valid():
      form.save()
      messages.success(request,'Coupon Added successfully')
      return redirect('adminCoupons')
    else:
      messages.error(request, 'Invalid input!!!')
      return redirect('adminAddCoupon')
  form = couponForm()
  context = {
    'form':form,
  }
  return render(request, 'adminPanel/couponManagement/adminAddCoupon.html', context)


@staff_member_required(login_url = 'adminLogin')
def adminEditCoupon(request, id):
  coupon = Coupon.objects.get(id = id)
  if request.method == 'POST':
    form = couponForm(request.POST , request.FILES, instance=coupon)
    if form.is_valid():
      form.save()
      messages.success(request,'Coupon updated successfully')
      return redirect('adminCoupons')
    else:
      messages.error(request, 'Invalid input!!!')
      return redirect('adminEditCoupon', coupon.id)
  form = couponForm(instance=coupon)
  context = {
    'coupon':coupon,
    'form':form,
  }
  return render(request, 'adminPanel/couponManagement/adminEditCoupon.html', context)


@staff_member_required(login_url= 'adminLogin')
def adminDeleteCoupon(request, id):
  coupon = Coupon.objects.get(id = id)
  coupon.delete()
  messages.success(request,'Coupon deleted successfully')
  return redirect('adminCoupons')


@staff_member_required(login_url= 'adminLogin')
def adminSalesData(request):
    total_orders = Order.objects.filter(is_ordered=True).order_by('created_at')
    first_order_date = total_orders[0].created_at.date()
    today = timezone.now()
    day = today.day
    month = today.month
    year = today.year
    month_list = []
    for i in range(1,13):month_list.append(calendar.month_name[i]) 
    year_list = []
    for i in range(first_order_date.year,year+1):year_list.append(i)
    this_date=str(today.date())
    start_date=this_date
    end_date=this_date
    filter= False
    
    if request.method == 'POST':
        start_date = request.POST.get('start_date')
        temp = start_date
        end_date = request.POST.get('end_date')
        # converting from naive to timezone aware
        val = timezone.make_aware(datetime.strptime(end_date, '%Y-%m-%d'))
        start_date = timezone.make_aware(datetime.strptime(temp, '%Y-%m-%d'))
        end_date = val+timedelta(days=1)
        filter=True
        orders = Order.objects.filter(Q(created_at__lte=end_date),Q(created_at__gte=start_date)).values('user_order_page__product__product_name','user_order_page__product__stock',total = Sum('order_total'),).annotate(dcount=Sum('user_order_page__quantity')).order_by('-total')
    else:
        orders = Order.objects.filter(created_at__year = year,created_at__month=month).values('user_order_page__product__product_name','user_order_page__product__stock',total = Sum('order_total'),).annotate(dcount=Sum('user_order_page__quantity')).order_by('-total')

    context = {
        'month_list':month_list,
        'orders':orders,
        'this_date':this_date,
        'year_list':year_list,
        'start_date':start_date,
        'end_date':end_date,
        'filter':filter
    }
    return render(request, 'adminPanel/adminSalesData.html', context)

