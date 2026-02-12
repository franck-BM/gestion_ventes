from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.contrib import messages
from .models import Produit, Client, Vente, LigneVente
from .forms import ProduitForm, ClientForm, VenteForm, LigneVenteFormSet
from django.db.models import F, Sum, Count
from vente import models as vente_models
from django.utils import timezone
from datetime import timedelta
import json
from django.http import HttpResponse
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
import io
from datetime import datetime
    


# -----------------------
# Dashboard
# -----------------------
@login_required
def tableau_bord(request):
    # Statistiques de base
    produits_count = Produit.objects.count()
    clients_count = Client.objects.count()
    ventes_count = Vente.objects.count()
    total_ca = sum([v.total for v in Vente.objects.all()])  # petit calcul
    
    # Statistiques de produits vendus
    produits_vendus = LigneVente.objects.aggregate(total=Sum('quantite'))['total'] or 0
    
    # Produits avec stock faible
    produits_seuil = Produit.objects.filter(stock__lte=F('seuil_alerte')).order_by('stock')
    
    # Top 5 produits les plus vendus
    top_produits = LigneVente.objects.values('produit__nom').annotate(
        quantite_totale=Sum('quantite')
    ).order_by('-quantite_totale')[:5]
    
    # Top 5 clients
    top_clients = Vente.objects.values('client__nom').annotate(
        nb_achats=Count('id'),
        montant_total=Sum('total')
    ).filter(client__isnull=False).order_by('-montant_total')[:5]
    
    # Ventes des 7 derniers jours
    date_debut = timezone.now() - timedelta(days=7)
    ventes_7j = Vente.objects.filter(date_vente__gte=date_debut)
    
    # Données pour graphique (ventes par jour)
    ventes_par_jour = {}
    for i in range(7):
        date = timezone.now() - timedelta(days=6-i)
        date_str = date.strftime('%d/%m')
        count = Vente.objects.filter(
            date_vente__date=date.date()
        ).aggregate(total=Sum('total'))['total'] or 0
        ventes_par_jour[date_str] = float(count)
    
    # Ventes par mois (12 derniers mois)
    ventes_par_mois = {}
    for i in range(12):
        date = timezone.now() - timedelta(days=30*i)
        mois_str = date.strftime('%b %Y')
        count = Vente.objects.filter(
            date_vente__year=date.year,
            date_vente__month=date.month
        ).aggregate(total=Sum('total'))['total'] or 0
        ventes_par_mois[mois_str] = float(count)
    
    context = {
        'produits_count': produits_count,
        'clients_count': clients_count,
        'ventes_count': ventes_count,
        'total_ca': total_ca,
        'produits_vendus': produits_vendus,
        'produits_seuil': produits_seuil,
        'top_produits': top_produits,
        'top_clients': top_clients,
        'ventes_7j': ventes_7j.count(),
        'ventes_par_jour': json.dumps(ventes_par_jour),
        'ventes_par_mois': json.dumps(ventes_par_mois),
        'produits_seuil_count': produits_seuil.count(),
    }
    return render(request, 'vente/dashboard.html', context)

# -----------------------
# Produits CRUD
# -----------------------
@login_required
def liste_produits(request):
    produits = Produit.objects.all().order_by('nom')
    return render(request, 'vente/produits.html', {'produits': produits})

@login_required
def ajouter_produit(request):
    if request.method == 'POST':
        form = ProduitForm(request.POST)
        if form.is_valid():
            produit = form.save()
            messages.success(request, f"Produit '{produit.nom}' ajouté.")
            return redirect('vente:liste_produits')
    else:
        form = ProduitForm()
    return render(request, 'vente/ajouter_produit.html', {'form': form})

@login_required
def modifier_produit(request, pk):
    produit = get_object_or_404(Produit, pk=pk)
    if request.method == 'POST':
        form = ProduitForm(request.POST, instance=produit)
        if form.is_valid():
            form.save()
            messages.success(request, "Produit modifié.")
            return redirect('vente:liste_produits')
    else:
        form = ProduitForm(instance=produit)
    return render(request, 'vente/modifier_produit.html', {'form': form, 'produit': produit})

@login_required
def supprimer_produit(request, pk):
    produit = get_object_or_404(Produit, pk=pk)
    if request.method == 'POST':
        produit.delete()
        messages.success(request, "Produit supprimé.")
        return redirect('vente:liste_produits')
    return render(request, 'vente/confirmer_suppression.html', {'objet': produit, 'type': 'produit'})

# -----------------------
# Clients CRUD
# -----------------------
@login_required
def liste_clients(request):
    clients = Client.objects.all().order_by('nom')
    return render(request, 'vente/clients.html', {'clients': clients})

@login_required
def ajouter_client(request):
    if request.method == 'POST':
        form = ClientForm(request.POST)
        if form.is_valid():
            client = form.save()
            messages.success(request, f"Client '{client.nom}' ajouté.")
            return redirect('vente:liste_clients')
    else:
        form = ClientForm()
    return render(request, 'vente/ajouter_client.html', {'form': form})

@login_required
def modifier_client(request, pk):
    client = get_object_or_404(Client, pk=pk)
    if request.method == 'POST':
        form = ClientForm(request.POST, instance=client)
        if form.is_valid():
            form.save()
            messages.success(request, "Client modifié.")
            return redirect('vente:liste_clients')
    else:
        form = ClientForm(instance=client)
    return render(request, 'vente/ajouter_client.html', {'form': form, 'client': client})

@login_required
def supprimer_client(request, pk):
    client = get_object_or_404(Client, pk=pk)
    if request.method == 'POST':
        client.delete()
        messages.success(request, "Client supprimé.")
        return redirect('vente:liste_clients')
    return render(request, 'vente/confirmer_suppression.html', {'objet': client, 'type': 'client'})

# -----------------------
# Ventes
# -----------------------
@login_required
def liste_ventes(request):
    ventes = Vente.objects.all().order_by('-date_vente')
    return render(request, 'vente/ventes.html', {'ventes': ventes})

@login_required
def creer_vente(request):
    if request.method == 'POST':
        form = VenteForm(request.POST)
        if form.is_valid():
            vente = form.save(commit=False)
            vente.total = 0
            vente.save()
            formset = LigneVenteFormSet(request.POST, instance=vente)
            if formset.is_valid():
                # Étape 1: Vérifier le stock disponible pour tous les articles
                stock_insuffisant = []
                lignes_a_creer = []
                
                for form_ligne in formset:
                    if form_ligne.cleaned_data and not form_ligne.cleaned_data.get('DELETE'):
                        produit = form_ligne.cleaned_data.get('produit')
                        quantite = form_ligne.cleaned_data.get('quantite', 0)
                        prix_unitaire = form_ligne.cleaned_data.get('prix_unitaire')
                        
                        if produit and quantite and quantite > 0:
                            if not produit.en_stock(quantite):
                                stock_insuffisant.append(
                                    f"{produit.nom}: {quantite} demandé(s) mais seulement {produit.stock} en stock"
                                )
                            else:
                                lignes_a_creer.append({
                                    'produit': produit,
                                    'quantite': quantite,
                                    'prix_unitaire': prix_unitaire or produit.prix
                                })
                
                # Si stock insuffisant, rejeter la vente
                if stock_insuffisant:
                    vente.delete()
                    for erreur in stock_insuffisant:
                        messages.error(request, erreur)
                    context = {
                        'form': form,
                        'formset': formset,
                        'produits': Produit.objects.all()
                    }
                    return render(request, 'vente/creer_vente.html', context)
                
                # Étape 2: Créer les lignes de vente et décrémenter le stock
                lignes_creees = []
                try:
                    for data_ligne in lignes_a_creer:
                        ligne = LigneVente.objects.create(
                            vente=vente,
                            produit=data_ligne['produit'],
                            quantite=data_ligne['quantite'],
                            prix_unitaire=data_ligne['prix_unitaire']
                        )
                        
                        # Décrémenter le stock immédiatement
                        produit = data_ligne['produit']
                        if produit.decrementer_stock(data_ligne['quantite']):
                            ligne.stock_deduit = True
                            ligne.save()
                            lignes_creees.append(ligne)
                        else:
                            raise Exception(f"Impossible de décrémenter le stock pour {produit.nom}")
                    
                    # Étape 3: Calculer le total
                    vente.calculer_total()
                    
                    # Étape 4: Afficher les avertissements de stock faible
                    for ligne in vente.lignes.all():
                        if ligne.produit.stock <= ligne.produit.seuil_alerte:
                            messages.warning(
                                request,
                                f"⚠️ Attention: {ligne.produit.nom} est en stock faible ({ligne.produit.stock} restant)"
                            )
                    
                    messages.success(request, f"✓ Vente #{vente.id} créée avec succès (Total: {vente.total})")
                    return redirect('vente:liste_ventes')
                    
                except Exception as e:
                    # En cas d'erreur, restaurer tous les stocks et supprimer la vente
                    for ligne in lignes_creees:
                        ligne.produit.restaurer_stock(ligne.quantite)
                    vente.delete()
                    messages.error(request, f"Erreur lors de la création de la vente: {str(e)}")
                    return redirect('vente:creer_vente')
            else:
                # Si formset invalide, supprimer la vente temporaire
                vente.delete()
                for error in formset.non_form_errors():
                    messages.error(request, error)
    else:
        form = VenteForm()
        formset = LigneVenteFormSet()
    
    # Afficher les produits avec stock faible sur la page
    produits_seuil = Produit.objects.filter(stock__lte=F('seuil_alerte')).order_by('stock')
    
    context = {
        'form': form,
        'formset': formset,
        'produits_seuil': produits_seuil,
        'produits': Produit.objects.all()
    }
    return render(request, 'vente/creer_vente.html', context)


# -----------------------
# Rapports et PDF
# -----------------------

@login_required
def clients_ayant_achete(request):
    """Liste les clients qui ont acheté avec leurs numéros de téléphone"""
    # Récupérer les clients qui ont au moins une vente
    clients_avec_achats = Client.objects.filter(
        vente__isnull=False
    ).distinct().annotate(
        nombre_achats=Count('vente'),
        montant_total=Sum('vente__total')
    ).order_by('-montant_total')
    
    context = {
        'clients': clients_avec_achats,
        'total_clients': clients_avec_achats.count(),
    }
    return render(request, 'vente/clients_achetes.html', context)


@login_required
def exporter_clients_pdf(request):
    """Exporte la liste des clients qui ont acheté en PDF"""
    # Récupérer les clients qui ont acheté
    clients = Client.objects.filter(
        vente__isnull=False
    ).distinct().annotate(
        nombre_achats=Count('vente'),
        montant_total=Sum('vente__total')
    ).order_by('-montant_total')
    
    # Créer la réponse PDF
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="rapport_clients.pdf"'
    
    # Créer le document PDF
    doc = SimpleDocTemplate(response, pagesize=A4)
    story = []
    styles = getSampleStyleSheet()
    
    # Titre
    title_style = ParagraphStyle(
        'Title',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=colors.HexColor('#2c3e50'),
        spaceAfter=30,
        alignment=TA_CENTER
    )
    story.append(Paragraph("RAPPORT DES CLIENTS", title_style))
    story.append(Spacer(1, 0.3*inch))
    
    # Date du rapport
    date_style = ParagraphStyle(
        'Date',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.grey,
        alignment=TA_RIGHT
    )
    story.append(Paragraph(f"Généré le: {datetime.now().strftime('%d/%m/%Y %H:%M')}", date_style))
    story.append(Spacer(1, 0.2*inch))
    
    # Statistiques
    stats_data = [
        ['Total de clients ayant acheté:', str(clients.count())],
        ['Nombre total d\'achats:', str(sum(c.nombre_achats for c in clients))],
        ['Montant total généré:', f"{sum(c.montant_total for c in clients if c.montant_total)}"]
    ]
    stats_table = Table(stats_data, colWidths=[3*inch, 2*inch])
    stats_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#ecf0f1')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 11),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
    ]))
    story.append(stats_table)
    story.append(Spacer(1, 0.3*inch))
    
    # Tableau des clients
    data = [['Nom', 'Téléphone', 'Email', 'Nombre d\'achats', 'Montant Total']]
    
    for client in clients:
        data.append([
            client.nom,
            client.telephone or '-',
            client.email or '-',
            str(client.nombre_achats),
            f"{client.montant_total:.2f} DZD" if client.montant_total else "0.00 DZD"
        ])
    
    # Créer le tableau
    table = Table(data, colWidths=[1.8*inch, 1.3*inch, 1.5*inch, 1.2*inch, 1.2*inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3498db')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#ecf0f1')]),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
    ]))
    
    story.append(table)
    story.append(Spacer(1, 0.3*inch))
    
    # Footer
    footer_style = ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.grey,
        alignment=TA_CENTER
    )
    story.append(Paragraph("Rapport généré automatiquement par le système de gestion des ventes", footer_style))
    
    # Générer le PDF
    doc.build(story)
    return response


@login_required
def exporter_ventes_pdf(request):
    """Exporte le rapport de ventes en PDF"""
    ventes = Vente.objects.all().select_related('client').prefetch_related('lignes__produit').order_by('-date_vente')
    
    # Créer la réponse PDF
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="rapport_ventes.pdf"'
    
    # Créer le document PDF
    doc = SimpleDocTemplate(response, pagesize=A4)
    story = []
    styles = getSampleStyleSheet()
    
    # Titre
    title_style = ParagraphStyle(
        'Title',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=colors.HexColor('#2c3e50'),
        spaceAfter=30,
        alignment=TA_CENTER
    )
    story.append(Paragraph("RAPPORT DE VENTES", title_style))
    story.append(Spacer(1, 0.3*inch))
    
    # Date du rapport
    date_style = ParagraphStyle(
        'Date',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.grey,
        alignment=TA_RIGHT
    )
    story.append(Paragraph(f"Généré le: {datetime.now().strftime('%d/%m/%Y %H:%M')}", date_style))
    story.append(Spacer(1, 0.2*inch))
    
    # Statistiques
    total_montant = sum(v.total for v in ventes)
    stats_data = [
        ['Total de ventes:', str(ventes.count())],
        ['Montant total généré:', f"{total_montant:.2f} DZD"],
        ['Nombre de lignes vendues:', str(LigneVente.objects.count())]
    ]
    stats_table = Table(stats_data, colWidths=[3*inch, 2*inch])
    stats_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#ecf0f1')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 11),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
    ]))
    story.append(stats_table)
    story.append(Spacer(1, 0.3*inch))
    
    # Tableau des ventes
    data = [['N° Vente', 'Client', 'Date', 'Montant', 'Produits']]
    
    for vente in ventes:
        produits = ', '.join([f"{l.produit.nom} (×{l.quantite})" for l in vente.lignes.all()])
        data.append([
            f"#{vente.id}",
            vente.client.nom if vente.client else 'N/A',
            vente.date_vente.strftime('%d/%m/%Y'),
            f"{vente.total:.2f} DZD",
            produits[:50] + '...' if len(produits) > 50 else produits
        ])
    
    # Créer le tableau
    table = Table(data, colWidths=[0.8*inch, 1.5*inch, 1.2*inch, 1*inch, 2.5*inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#27ae60')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#ecf0f1')]),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
    ]))
    
    story.append(table)
    story.append(Spacer(1, 0.3*inch))
    
    # Footer
    footer_style = ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.grey,
        alignment=TA_CENTER
    )
    story.append(Paragraph("Rapport généré automatiquement par le système de gestion des ventes", footer_style))
    
    # Générer le PDF
    doc.build(story)
    return response
