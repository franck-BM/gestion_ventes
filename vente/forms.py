from django import forms
from .models import Produit, Client, Vente, LigneVente
from django.forms import inlineformset_factory

class ProduitForm(forms.ModelForm):
    class Meta:
        model = Produit
        fields = ['nom', 'description', 'prix', 'stock', 'seuil_alerte']

class ClientForm(forms.ModelForm):
    class Meta:
        model = Client
        fields = ['nom', 'email', 'telephone', 'adresse']

class VenteForm(forms.ModelForm):
    class Meta:
        model = Vente
        fields = ['client', 'paiement_effectue']

LigneVenteFormSet = inlineformset_factory(
    Vente, LigneVente,
    fields=('produit', 'quantite', 'prix_unitaire'),
    extra=1, can_delete=True
)
