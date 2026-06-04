from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from shop.models import Product, Order, Customer
from django.db.models import Sum, Count


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_products(request):
    qs = Product.objects.filter(is_available=True).values(
        'id','name','price','unit','product_type__name','is_available')
    return Response(list(qs))


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_product_detail(request, pk):
    try:
        p = Product.objects.get(pk=pk)
    except Product.DoesNotExist:
        return Response({'error': 'Not found'}, status=404)
    return Response({
        'id': p.pk, 'name': p.name, 'price': str(p.price),
        'unit': p.get_unit_display(), 'type': p.product_type.name,
        'description': p.description, 'is_available': p.is_available,
        'created_at': p.created_at.strftime('%d/%m/%Y'),
    })


@api_view(['GET'])
@permission_classes([IsAdminUser])
def api_statistics(request):
    return Response({
        'total_products': Product.objects.count(),
        'total_orders': Order.objects.count(),
        'delivered_orders': Order.objects.filter(status='delivered').count(),
        'total_customers': Customer.objects.count(),
        'total_revenue': str(Order.objects.filter(status='delivered').aggregate(
            s=Sum('total_price'))['s'] or 0),
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_my_orders(request):
    user = request.user
    if user.is_client():
        try:
            orders = Order.objects.filter(customer=user.customer_profile).values(
                'id','status','total_price','order_date','delivery_type')
            return Response(list(orders))
        except Exception:
            return Response([])
    elif user.is_employee() or user.is_staff:
        try:
            orders = Order.objects.filter(employee=user.employee_profile).values(
                'id','customer__last_name','status','total_price','order_date')
            return Response(list(orders))
        except Exception:
            return Response([])
    return Response({'error': 'Forbidden'}, status=403)
