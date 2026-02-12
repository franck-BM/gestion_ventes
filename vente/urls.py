from django.urls import path
from . import views

app_name = 'vente'

urlpatterns = [
    path('', views.tableau_bord, name='tableau_bord'),

    # Produits
    path('produits/', views.liste_produits, name='liste_produits'),
    path('produits/ajouter/', views.ajouter_produit, name='ajouter_produit'),
    path('produits/modifier/<int:pk>/', views.modifier_produit, name='modifier_produit'),
    path('produits/supprimer/<int:pk>/', views.supprimer_produit, name='supprimer_produit'),

    # Clients
    path('clients/', views.liste_clients, name='liste_clients'),
    path('clients/ajouter/', views.ajouter_client, name='ajouter_client'),
    path('clients/modifier/<int:pk>/', views.modifier_client, name='modifier_client'),
    path('clients/supprimer/<int:pk>/', views.supprimer_client, name='supprimer_client'),

    # Ventes
    path('ventes/', views.liste_ventes, name='liste_ventes'),
    path('ventes/creer/', views.creer_vente, name='creer_vente'),
    
    # Rapports
    path('clients-achetes/', views.clients_ayant_achete, name='clients_achetes'),
    path('export/clients-pdf/', views.exporter_clients_pdf, name='exporter_clients_pdf'),
    path('export/ventes-pdf/', views.exporter_ventes_pdf, name='exporter_ventes_pdf'),
]
