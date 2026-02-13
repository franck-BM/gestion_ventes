from django.core.management.base import BaseCommand
from django.db.models import Count, Q
from vente.models import Produit, Client, Vente, LigneVente


class Command(BaseCommand):
    help = 'Supprime les doublons de produits, clients et ventes'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('🧹 Début du nettoyage des doublons...'))
        
        # Supprimer les doublons de produits
        self.remove_duplicate_produits()
        
        # Supprimer les doublons de clients
        self.remove_duplicate_clients()
        
        # Supprimer les doublons de lignes vente
        self.remove_duplicate_lignes_vente()
        
        self.stdout.write(self.style.SUCCESS('✅ Nettoyage terminé!'))

    def remove_duplicate_produits(self):
        """Supprime les produits en doublon basé sur le nom"""
        self.stdout.write('\n📦 Traitement des produits...')
        
        produits_dupes = Produit.objects.values('nom').annotate(
            count=Count('id')
        ).filter(count__gt=1)
        
        total_supprimés = 0
        for dupe in produits_dupes:
            nom = dupe['nom']
            # Garder le premier, supprimer les autres
            produits = Produit.objects.filter(nom=nom).order_by('id')
            premier = produits.first()
            
            # Fusionner les stocks
            stock_total = produits.aggregate(stock_total=Count('id'))
            total_stock = sum(p.stock for p in produits)
            premier.stock = total_stock
            premier.save()
            
            # Supprimer les doublons
            supprimés = produits.exclude(id=premier.id).delete()[0]
            total_supprimés += supprimés
            self.stdout.write(f"  ✓ Produit '{nom}': {supprimés} doublon(s) supprimé(s)")
        
        if total_supprimés == 0:
            self.stdout.write('  ℹ️  Aucun doublon de produit trouvé')
        else:
            self.stdout.write(self.style.WARNING(f'  → Total: {total_supprimés} produits supprimés'))

    def remove_duplicate_clients(self):
        """Supprime les clients en doublon basé sur le nom"""
        self.stdout.write('\n👥 Traitement des clients...')
        
        clients_dupes = Client.objects.values('nom').annotate(
            count=Count('id')
        ).filter(count__gt=1)
        
        total_supprimés = 0
        for dupe in clients_dupes:
            nom = dupe['nom']
            # Garder le premier, supprimer les autres
            clients = Client.objects.filter(nom=nom).order_by('id')
            premier = clients.first()
            
            # Fusionner les ventes
            for client in clients.exclude(id=premier.id):
                Vente.objects.filter(client=client).update(client=premier)
            
            # Supprimer les doublons
            supprimés = clients.exclude(id=premier.id).delete()[0]
            total_supprimés += supprimés
            self.stdout.write(f"  ✓ Client '{nom}': {supprimés} doublon(s) supprimé(s)")
        
        if total_supprimés == 0:
            self.stdout.write('  ℹ️  Aucun doublon de client trouvé')
        else:
            self.stdout.write(self.style.WARNING(f'  → Total: {total_supprimés} clients supprimés'))

    def remove_duplicate_lignes_vente(self):
        """Supprime les lignes de vente en doublon"""
        self.stdout.write('\n🛒 Traitement des lignes de vente...')
        
        total_supprimés = 0
        
        # Trouver les lignes en doublon (même vente + même produit)
        ventes = Vente.objects.all()
        for vente in ventes:
            lignes_dupes = vente.lignes.values('produit').annotate(
                count=Count('id')
            ).filter(count__gt=1)
            
            for dupe in lignes_dupes:
                produit_id = dupe['produit']
                lignes = vente.lignes.filter(produit_id=produit_id).order_by('id')
                premiere = lignes.first()
                
                # Fusionner les quantités
                quantite_totale = sum(l.quantite for l in lignes)
                premiere.quantite = quantite_totale
                premiere.save()
                
                # Supprimer les doublons
                supprimés = lignes.exclude(id=premiere.id).delete()[0]
                total_supprimés += supprimés
        
        if total_supprimés == 0:
            self.stdout.write('  ℹ️  Aucun doublon de ligne trouvé')
        else:
            self.stdout.write(self.style.WARNING(f'  → Total: {total_supprimés} lignes supprimées'))
