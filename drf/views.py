from inventory.models import Product, Comment, Profile, Order, OrderProduct, RentProduct
from rest_framework import viewsets, permissions, mixins
from drf.serializer import AllProducts, UserSerializer, CommentSerializer,RentProductSerializer ,ProfileSerializer, OrderSerializer, OrderProductSerializer, CategorySerializer
from rest_framework.response import Response
from rest_framework.authentication import TokenAuthentication
from django.contrib.auth.models import User
from rest_framework.pagination import PageNumberPagination
from django.core.mail import send_mail
from django.template.loader import render_to_string
"""
views.py służą do definiowania dynamicznie generowanych widoków, które potem przy pomocy url.py są przypisane do okreslonego adresu URL
"""

class ReadOnly(permissions.BasePermission):
  
    def has_object_permission(self, request, view, obj):
           return request.method in permissions.SAFE_METHODS
       
class StandardResultsSetPagination(PageNumberPagination):
    page_size = 30
    


class AllProductsViewSet(viewsets.ModelViewSet): 
    ##lista wszystkich produktów /api/
   
    serializer_class = AllProducts
    pagination_class = StandardResultsSetPagination
    authentication_class = (TokenAuthentication,)
    permission_classes = [ReadOnly]
    lookup_field = "slug"
    http_method_names = ['get', 'head']
    def get_queryset(self):
        """
        Optionally restricts the returned purchases to a given user,
        by filtering against a `product` query parameter in the URL.
        """
        queryset = Product.objects.all().filter(is_active=True).order_by('id')
        category = self.request.query_params.get('category') 
        rent = self.request.query_params.get('active')
        name = self.request.query_params.get('name')       
        if category is not None: 
            queryset = queryset.filter(category__name=category) 
        if name is not None: ##do zwracania produktów z kategorią 
            queryset = queryset.filter(name__icontains=name) 
        if rent is not None: 
            queryset = queryset.filter(displayrent=True).filter(renteduntill=None)           
        return queryset



class RentReadyProducts(viewsets.ModelViewSet):
    ##lista produktów które uczestniczą w wypożyczalni i nie są aktualnie wypożyczone /rentready/
    serializer_class = AllProducts
    http_method_names = ['get','head']
    def get_queryset(self):
       
        queryset = Product.objects.all().order_by('id')
        queryset = queryset.filter(displayrent=True).filter(renteduntill=None)
        return queryset
    


class UserViewSet(viewsets.ModelViewSet):
    ##do rejestracji użytkowników /users/
    queryset = User.objects.all()
    serializer_class = UserSerializer    
    http_method_names = ['post',"get", 'head']

class ProfileViewSet(viewsets.ModelViewSet):
    ##indywidualne informacje dostepne tylko dla zalogowanego użytkownika /profile/
    queryset=Profile.objects.all().order_by('id')
    serializer_class = ProfileSerializer   
    lookup_field = "user__username"
    http_method_names = ['get', 'head']
   
    def get_queryset(self): 
     return Profile.objects.filter(user=self.request.user) #zwróć obiekty gdzie user w modelu zgadza sie z userem z requesta (wymaga tokenu)
        
      
   
class OrderViewSet(viewsets.ModelViewSet):
    ##dane dot zamówienia
    queryset = Order.objects.all().order_by('id')
    serializer_class = OrderSerializer
    authentication_class = (TokenAuthentication,)
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    http_method_names = ['post','get', 'head']

    def get_queryset(self): 
     order = Order.objects.filter(owner=Profile.objects.get(user=self.request.user)).order_by('id').last()
     body = f'Użytkowniku "{self.request.user.username}" twoje zamówienie na kwotę {order.price}zł zostało pomyślnie złożone. \n\n'
     body += f'Adres zamówienia: {order.city} ul. {order.street}, {order.zipcode} \n\nZakupiono: \n'
     for product in order.OrderProduct.all():
        body += f'{product.product.name} {product.product.price} zł za sztukę, sztuk: {product.quantity}\n'

     
     send_mail(
        f'Twoje zamówienie o numerze {order.id} zostało złożone!',
        body,
        'djangojopek@gmail.com',
        [f'{self.request.user.email}'],
        fail_silently=False,
        )
     return Order.objects.filter(owner=Profile.objects.get(user=self.request.user))#zwróć obiekty gdzie user w modelu zgadza sie z userem z requesta (wymaga tokenu)
    
    def perform_create(self, serializer):     
         serializer.save(owner=Profile.objects.get(user=self.request.user))       
        
        
class OrderProductViewSet(viewsets.ModelViewSet):
    ##powiązane zamówienia i produkty
    queryset = OrderProduct.objects.all().order_by('id')
    serializer_class = OrderProductSerializer
    authentication_class = (TokenAuthentication,)
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    http_method_names = ['post', 'head']

  
    
class CommentsViewSet(viewsets.ModelViewSet):
    ##lista komentarzy
    serializer_class = CommentSerializer
    authentication_class = (TokenAuthentication,)
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    lookup_field = "id"
    
    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)
    
    def get_queryset(self):
        queryset = Comment.objects.all().order_by('-id')
        product = self.request.query_params.get('product') 
        owner = self.request.query_params.get('owner') 
        if product is not None: ##do zwracania komentarzy napisanych pod danym produktem
            queryset = queryset.filter(product=product)
        if owner is not None: ##do zwracania komentarzy napisanych tylko przez danego użytk
            queryset = queryset.filter(owner__username=owner)
        return queryset


class RentProductViewSet(viewsets.ModelViewSet):
    ##która pozycja wypożyczona przez kogo 
    queryset = RentProduct.objects.all().order_by('id')
    serializer_class = RentProductSerializer
    authentication_class = (TokenAuthentication,)
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    http_method_names = ['post', 'head']
    
    def perform_create(self, serializer):
        
        
        serializer.save(owner=Profile.objects.get(user=self.request.user))