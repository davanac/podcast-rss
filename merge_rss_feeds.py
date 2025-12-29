#!/usr/bin/env python3
"""
Script de fusion des flux RSS : Anchor + Ghost
Combine les épisodes existants d'Anchor avec les nouveaux générés depuis Ghost
"""

import xml.etree.ElementTree as ET
from pathlib import Path
from datetime import datetime
import requests

# Configuration
SCRIPT_DIR = Path(__file__).parent
ANCHOR_RSS_FILE = SCRIPT_DIR / "anchor_rss_backup.xml"
GHOST_RSS_FILE = SCRIPT_DIR / "podcast.rss"
MERGED_RSS_FILE = SCRIPT_DIR / "podcast_merged.rss"

# URL du flux Anchor (pour télécharger la dernière version)
ANCHOR_RSS_URL = "https://anchor.fm/s/9090b10/podcast/rss"


class RSSMerger:
    def __init__(self):
        self.anchor_episodes = []
        self.ghost_episodes = []

    def download_anchor_rss(self):
        """Télécharge la dernière version du flux Anchor"""
        print("📥 Téléchargement du flux RSS Anchor...")
        try:
            response = requests.get(ANCHOR_RSS_URL, timeout=30)
            response.raise_for_status()

            with open(ANCHOR_RSS_FILE, 'wb') as f:
                f.write(response.content)

            print(f"✅ Flux Anchor téléchargé : {ANCHOR_RSS_FILE}")
            return True
        except Exception as e:
            print(f"❌ Erreur téléchargement Anchor RSS : {e}")
            return False

    def parse_anchor_rss(self):
        """Parse le flux RSS Anchor et extrait les épisodes"""
        print("\n📖 Lecture du flux Anchor...")

        try:
            tree = ET.parse(ANCHOR_RSS_FILE)
            root = tree.getroot()

            # Parcourir tous les <item> (épisodes)
            for item in root.findall('.//item'):
                episode = {
                    'element': item,
                    'title': self._get_text(item, 'title'),
                    'guid': self._get_text(item, 'guid'),
                    'pubDate': self._get_text(item, 'pubDate'),
                    'source': 'anchor'
                }
                self.anchor_episodes.append(episode)

            print(f"✅ {len(self.anchor_episodes)} épisodes Anchor trouvés")
            return True

        except Exception as e:
            print(f"❌ Erreur lecture Anchor RSS : {e}")
            return False

    def parse_ghost_rss(self):
        """Parse le flux RSS Ghost et extrait les épisodes"""
        print("\n📖 Lecture du flux Ghost...")

        if not GHOST_RSS_FILE.exists():
            print(f"⚠️  Fichier Ghost RSS introuvable : {GHOST_RSS_FILE}")
            return False

        try:
            tree = ET.parse(GHOST_RSS_FILE)
            root = tree.getroot()

            # Parcourir tous les <item> (épisodes)
            for item in root.findall('.//item'):
                episode = {
                    'element': item,
                    'title': self._get_text(item, 'title'),
                    'guid': self._get_text(item, 'guid'),
                    'pubDate': self._get_text(item, 'pubDate'),
                    'source': 'ghost'
                }
                self.ghost_episodes.append(episode)

            print(f"✅ {len(self.ghost_episodes)} épisodes Ghost trouvés")
            return True

        except Exception as e:
            print(f"❌ Erreur lecture Ghost RSS : {e}")
            return False

    def _get_text(self, element, tag):
        """Récupère le texte d'un élément XML"""
        child = element.find(tag)
        if child is not None:
            return child.text
        return None

    def merge_feeds(self):
        """Fusionne les deux flux RSS"""
        print("\n🔄 Fusion des flux RSS...")

        try:
            # Enregistrer les namespaces pour garder les préfixes corrects
            ET.register_namespace('itunes', 'http://www.itunes.com/dtds/podcast-1.0.dtd')
            ET.register_namespace('atom', 'http://www.w3.org/2005/Atom')
            ET.register_namespace('content', 'http://purl.org/rss/1.0/modules/content/')
            ET.register_namespace('dc', 'http://purl.org/dc/elements/1.1/')

            # Parser le flux Anchor comme base
            tree = ET.parse(ANCHOR_RSS_FILE)
            root = tree.getroot()
            channel = root.find('channel')

            # Mettre à jour les métadonnées du podcast
            self._update_channel_metadata(channel)

            # Supprimer tous les <item> existants
            for item in channel.findall('item'):
                channel.remove(item)

            # Créer une liste combinée d'épisodes avec déduplication par GUID
            all_episodes = []
            seen_guids = set()

            # Ajouter les épisodes Ghost en premier (les plus récents)
            # Si doublon GUID, Ghost a priorité sur Anchor
            ghost_tree = ET.parse(GHOST_RSS_FILE)
            for item in ghost_tree.findall('.//item'):
                guid = self._get_text(item, 'guid')
                if guid and guid not in seen_guids:
                    all_episodes.append({
                        'element': item,
                        'guid': guid,
                        'pubDate': self._get_text(item, 'pubDate'),
                        'source': 'ghost'
                    })
                    seen_guids.add(guid)

            # Ajouter les épisodes Anchor (sauf si GUID déjà présent)
            anchor_tree = ET.parse(ANCHOR_RSS_FILE)
            for item in anchor_tree.findall('.//item'):
                guid = self._get_text(item, 'guid')
                if guid and guid not in seen_guids:
                    all_episodes.append({
                        'element': item,
                        'guid': guid,
                        'pubDate': self._get_text(item, 'pubDate'),
                        'source': 'anchor'
                    })
                    seen_guids.add(guid)

            # Trier par date de publication (plus récent en premier)
            all_episodes.sort(
                key=lambda x: self._parse_date(x['pubDate']),
                reverse=True
            )

            # Ajouter tous les épisodes au channel
            print(f"\n📊 Ajout de {len(all_episodes)} épisodes au flux fusionné :")

            for i, episode in enumerate(all_episodes, 1):
                channel.append(episode['element'])
                title = self._get_text(episode['element'], 'title')
                source = episode['source']
                print(f"   {i}. [{source.upper()}] {title[:70]}...")

            # Sauvegarder le flux fusionné
            tree.write(
                MERGED_RSS_FILE,
                encoding='utf-8',
                xml_declaration=True
            )

            # Reformater avec minidom pour un XML propre
            self._prettify_xml(MERGED_RSS_FILE)

            print(f"\n✅ Flux RSS fusionné : {MERGED_RSS_FILE}")
            print(f"   📊 Total : {len(all_episodes)} épisodes")
            print(f"   🆕 Ghost : {len(self.ghost_episodes)} épisodes")
            print(f"   📻 Anchor : {len(self.anchor_episodes)} épisodes")

            return True

        except Exception as e:
            print(f"❌ Erreur fusion RSS : {e}")
            import traceback
            traceback.print_exc()
            return False

    def _update_channel_metadata(self, channel):
        """Met à jour les métadonnées du channel pour conformité Apple Podcasts"""
        # Mettre à jour la description du podcast
        description = channel.find('description')
        if description is not None:
            new_description = """Veille quotidienne sur la liberté numérique

2-3 épisodes par jour :
→ Analyses tech/politique/surveillance
→ Des pistes d'action concrètes et des trajectoires possibles à expérimenter
→ Ce que j'explore en coulisses (projets, échecs, apprentissages)

Philosophie : Comprendre les systèmes avant de s'en libérer.
Pas de panique. Pas de défaitisme. De la lucidité. De l'action.

Newsletter hebdo + Discord : https://da.van.ac"""
            description.text = new_description
            print(f"   ✓ Description du podcast mise à jour")

        # Mettre à jour lastBuildDate
        lastBuildDate = channel.find('lastBuildDate')
        if lastBuildDate is not None:
            now = datetime.utcnow()
            lastBuildDate.text = now.strftime('%a, %d %b %Y %H:%M:%S GMT')

        # Mettre à jour atom:link rel="self" avec la nouvelle URL
        atom_ns = '{http://www.w3.org/2005/Atom}'

        # Chercher tous les atom:link
        for link in channel.findall(f'{atom_ns}link'):
            if link.get('rel') == 'self':
                # Mettre à jour l'URL
                old_url = link.get('href')
                link.set('href', 'https://davanac.github.io/podcast-rss/podcast_merged.rss')
                print(f"   ✓ Mise à jour de atom:link rel='self'")
                print(f"     Ancien : {old_url}")
                print(f"     Nouveau : https://davanac.github.io/podcast-rss/podcast_merged.rss")
                break
        else:
            # Si pas trouvé, créer
            self_link = ET.Element(f'{atom_ns}link')
            self_link.set('href', 'https://davanac.github.io/podcast-rss/podcast_merged.rss')
            self_link.set('rel', 'self')
            self_link.set('type', 'application/rss+xml')
            # Insérer après le lastBuildDate
            insert_index = list(channel).index(lastBuildDate) + 1
            channel.insert(insert_index, self_link)
            print(f"   ✓ Ajout de atom:link rel='self'")

        # Vérifier itunes:category
        itunes_ns = '{http://www.itunes.com/dtds/podcast-1.0.dtd}'
        itunes_category = channel.find(f'{itunes_ns}category')
        if itunes_category is None:
            print(f"   ⚠️  itunes:category manquante (devrait être présente dans Anchor)")

        # Vérifier itunes:explicit
        itunes_explicit = channel.find(f'{itunes_ns}explicit')
        if itunes_explicit is None:
            print(f"   ⚠️  itunes:explicit manquante (devrait être présente dans Anchor)")

        # Vérifier itunes:image
        itunes_image = channel.find(f'{itunes_ns}image')
        if itunes_image is None:
            print(f"   ⚠️  itunes:image manquante (devrait être présente dans Anchor)")

        # Vérifier itunes:author
        itunes_author = channel.find(f'{itunes_ns}author')
        if itunes_author is None:
            # Ajouter itunes:author si manquant
            itunes_author = ET.Element(f'{itunes_ns}author')
            itunes_author.text = 'Damien Van Achter (davanac)'
            channel.append(itunes_author)
            print(f"   ✓ Ajout de itunes:author")

    def _parse_date(self, date_str):
        """Parse une date RFC 2822 en objet datetime"""
        if not date_str:
            return datetime.min

        try:
            # Format RFC 2822 : "Mon, 22 Dec 2025 12:45:50 +0000"
            from email.utils import parsedate_to_datetime
            return parsedate_to_datetime(date_str)
        except:
            return datetime.min

    def _prettify_xml(self, filepath):
        """Reformate le XML avec minidom pour un affichage propre"""
        try:
            from xml.dom import minidom

            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()

            dom = minidom.parseString(content)
            pretty_xml = dom.toprettyxml(indent="  ", encoding='utf-8')

            with open(filepath, 'wb') as f:
                f.write(pretty_xml)

        except Exception as e:
            print(f"⚠️  Erreur formatage XML : {e}")

    def run(self):
        """Exécute le processus complet de fusion"""
        print("=" * 60)
        print("🔄 FUSION DES FLUX RSS : ANCHOR + GHOST")
        print("=" * 60)

        # Télécharger le flux Anchor
        if not self.download_anchor_rss():
            return False

        # Parser les deux flux
        if not self.parse_anchor_rss():
            return False

        if not self.parse_ghost_rss():
            return False

        # Fusionner
        if not self.merge_feeds():
            return False

        print("\n" + "=" * 60)
        print("✅ FUSION TERMINÉE AVEC SUCCÈS")
        print("=" * 60)
        print(f"\n📡 Fichier final : {MERGED_RSS_FILE}")
        print(f"\n💡 Prochaines étapes :")
        print(f"   1. Vérifier le fichier : cat {MERGED_RSS_FILE}")
        print(f"   2. Valider le RSS : https://podba.se/validate/")
        print(f"   3. Héberger sur GitHub Pages ou Netlify")
        print(f"   4. Rediriger depuis Spotify for Creators")
        print()

        return True


if __name__ == "__main__":
    merger = RSSMerger()
    merger.run()
