from django.db import models
from django.urls import reverse
from django.utils import timezone
from decimal import Decimal

class Client(models.Model):
    nom = models.CharField(max_length=150)
    email = models.EmailField(blank=True)
    telephone = models.CharField(max_length=30, blank=True)
    adresse = models.TextField(blank=True)

    def __str__(self):
        return self.nom

class Produit(models.Model):
    nom = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    prix = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField(default=0)
    seuil_alerte = models.PositiveIntegerField(default=5)  # alerte stock faible

    def __str__(self):
        return self.nom

    def en_stock(self, quantite=1):
        return self.stock >= quantite

    def decrementer_stock(self, quantite=1):
        """Diminue le stock du produit"""
        if quantite <= 0:
            return False
        if not self.en_stock(quantite):
            return False
        self.stock = max(0, self.stock - quantite)
        self.save()
        return True

    def restaurer_stock(self, quantite=1):
        """Restaure le stock du produit (en cas d'annulation)"""
        if quantite <= 0:
            return
        self.stock += quantite
        self.save()

class Vente(models.Model):
    client = models.ForeignKey(Client, on_delete=models.SET_NULL, null=True, blank=True)
    date_vente = models.DateTimeField(default=timezone.now)
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    paiement_effectue = models.BooleanField(default=False)

    def __str__(self):
        return f"Vente #{self.id} - {self.client.nom if self.client else 'Client inconnu'}"

    def calculer_total(self):
        total = Decimal('0.00')
        for ligne in self.lignes.all():
            total += ligne.total_ligne()
        self.total = total
        self.save()
        return self.total

class LigneVente(models.Model):
    vente = models.ForeignKey(Vente, on_delete=models.CASCADE, related_name='lignes')
    produit = models.ForeignKey(Produit, on_delete=models.PROTECT)
    quantite = models.PositiveIntegerField(default=1)
    prix_unitaire = models.DecimalField(max_digits=10, decimal_places=2)
    stock_deduit = models.BooleanField(default=False)  # Tracker si stock a déjà été déduit

    def __str__(self):
        return f"{self.produit.nom} x {self.quantite}"

    def total_ligne(self):
        return self.prix_unitaire * self.quantite

    def save(self, *args, **kwargs):
        # S'assurer que prix_unitaire est défini si vide
        if not self.prix_unitaire:
            self.prix_unitaire = self.produit.prix
        super().save(*args, **kwargs)
