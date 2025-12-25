# Automatisation complète du Podcast Ghost + Anchor vers Spotify

## Workflow automatisé configuré

Votre système est maintenant **entièrement automatisé** pour publier vos podcasts sur Spotify.

---

## Flux de travail complet

```
Article Ghost (scheduled)
         ↓
ghost_audio_generator.py détecte l'article (automatique via launchd)
         ↓
Génération audio via Eleven Labs
         ↓
Upload MP3 sur Ghost
         ↓
Ajout du player audio dans l'article
         ↓
🆕 Génération du flux RSS Ghost (podcast.rss)
         ↓
🔄 Fusion automatique avec les épisodes Anchor (podcast_merged.rss)
         ↓
📤 Publication automatique sur GitHub (auto_publish_rss.sh)
         ↓
✅ Commit + Push vers GitHub Pages
         ↓
⏱️ Spotify interroge le RSS (6-24h)
         ↓
🎉 Nouvel épisode disponible sur Spotify !
```

---

## Fichiers impliqués

### Scripts principaux

1. **`ghost_audio_generator.py`**
   - Génère l'audio depuis Ghost
   - Upload le MP3
   - Déclenche la fusion RSS
   - Déclenche la publication GitHub

2. **`podcast_rss_generator.py`**
   - Génère le flux RSS Ghost seul
   - Récupère titre, description, image, MP3

3. **`merge_rss_feeds.py`**
   - Télécharge le flux Anchor (241 épisodes historiques)
   - Fusionne avec les nouveaux épisodes Ghost
   - Trie par date (plus récent en premier)
   - Génère `podcast_merged.rss` (259 épisodes au total)

4. **`auto_publish_rss.sh`**
   - Exécute la fusion complète
   - Commit les changements
   - Push vers GitHub Pages
   - Affiche les statistiques

### Fichiers de données

- **`podcast.rss`** : Flux RSS Ghost seul (épisodes récents)
- **`podcast_merged.rss`** : Flux RSS fusionné Anchor + Ghost (tous les épisodes)
- **`anchor_rss_backup.xml`** : Backup du flux Anchor (téléchargé à chaque fusion)
- **`.processed_audio.json`** : Fichier de suivi des articles traités

---

## URLs importantes

### Flux RSS final
```
https://davanac.github.io/podcast-rss/podcast_merged.rss
```

**IMPORTANT** : Cette URL est déjà configurée dans Spotify for Creators.
Spotify interroge automatiquement ce flux toutes les 6-24h pour détecter les nouveaux épisodes.

### Repository GitHub
```
https://github.com/davanac/podcast-rss
```

### Podcast Spotify
```
https://open.spotify.com/show/028XGbXQzfUBCjiiWIrADE
```

---

## Exécution manuelle

### Générer audio + RSS + Publication GitHub
```bash
cd /Users/davanac/Documents/lab/Claude/projets/ghost-audio-system
python3 ghost_audio_generator.py
```

Ce script fait **tout automatiquement** :
- Détecte les nouveaux articles Ghost
- Génère l'audio
- Upload sur Ghost
- Génère le RSS Ghost
- Fusionne avec Anchor
- Publie sur GitHub

### Fusion + Publication seule (sans génération audio)
```bash
./auto_publish_rss.sh
```

Utile si vous voulez juste mettre à jour le flux RSS sans générer de nouveaux audios.

---

## Vérifications

### Vérifier le nombre d'épisodes
```bash
grep -c "<item>" podcast_merged.rss
```

Résultat actuel : **259 épisodes**

### Vérifier les derniers commits
```bash
git log -3 --oneline
```

### Tester l'URL RSS publique
```bash
curl -s "https://raw.githubusercontent.com/davanac/podcast-rss/main/podcast_merged.rss" | grep -c "<item>"
```

---

## Statistiques actuelles

- **Total d'épisodes** : 259
- **Épisodes Anchor** : 241 (historique)
- **Épisodes Ghost** : 18 (nouveaux, générés automatiquement)
- **Dernière publication** : 2025-12-26 00:30:53
- **Commit** : `ca65364`

---

## Automatisation quotidienne (launchd)

Le script `ghost_audio_generator.py` s'exécute automatiquement tous les jours à 9h00 via launchd.

### Vérifier le service
```bash
launchctl list | grep ghost.audio
```

### Voir les logs
```bash
tail -30 logs/launchd_audio.log
```

### Relancer manuellement
```bash
launchctl start ghost.audio
```

---

## Prochaines étapes IMPORTANTES

### 1. Configurer l'URL RSS dans Spotify

**Action requise** : Vous devez mettre à jour l'URL RSS dans Spotify for Creators.

1. Connectez-vous : https://creators.spotify.com/pod/profile/davanac/
2. Settings → RSS feed
3. **Remplacez l'ancienne URL par** :
   ```
   https://raw.githubusercontent.com/davanac/podcast-rss/main/podcast_merged.rss
   ```
4. Sauvegardez
5. Attendez 6-24h pour que Spotify détecte les changements

### 2. Vérifier la mise à jour

Après 24h :
- Vérifiez que les 259 épisodes apparaissent sur Spotify
- Testez la lecture des nouveaux épisodes
- Vérifiez que les métadonnées sont correctes (titres, descriptions, images)

---

## Dépannage

### Le RSS n'est pas mis à jour sur GitHub

1. Vérifiez que le commit a été créé :
   ```bash
   git log -1 --stat
   ```

2. Vérifiez que le push a réussi :
   ```bash
   git status
   ```
   Devrait afficher : "Your branch is up to date with 'origin/main'"

3. Attendez 2-5 minutes pour que GitHub Pages build

### Spotify ne détecte pas les changements

- Attendez 24-48h (Spotify est lent)
- L'URL RSS configurée dans Spotify : https://davanac.github.io/podcast-rss/podcast_merged.rss
- Testez l'URL RSS : https://podba.se/validate/
- Vérifiez les logs Spotify : https://creators.spotify.com/pod/profile/davanac/

### GitHub Pages n'affiche pas tous les épisodes

Si GitHub Pages affiche moins de 259 épisodes :
- Attendez 5-10 minutes (GitHub Pages doit reconstruire le site)
- Vérifiez que le fichier sur GitHub contient bien tous les épisodes :
  ```bash
  curl -s "https://raw.githubusercontent.com/davanac/podcast-rss/main/podcast_merged.rss" | grep -c "<item>"
  ```
- GitHub Pages se met à jour automatiquement après chaque push

### Erreur lors de la fusion

Si `merge_rss_feeds.py` échoue :
```bash
python3 merge_rss_feeds.py
```

Cela téléchargera la dernière version du flux Anchor et refera la fusion.

---

## Maintenance

### Sauvegarder le flux Anchor

Le flux Anchor est téléchargé automatiquement à chaque fusion, mais vous pouvez le sauvegarder manuellement :
```bash
cp anchor_rss_backup.xml anchor_rss_backup_$(date +%Y%m%d).xml
```

### Nettoyer les anciens fichiers audio

Les fichiers MP3 générés sont dans `audio_files/`. Vous pouvez les supprimer si besoin (ils sont déjà uploadés sur Ghost).

---

## Contact et support

- **GitHub Issues** : https://github.com/davanac/podcast-rss/issues
- **Spotify Support** : https://creators.spotify.com/pod/help

---

**Date de configuration** : 26 décembre 2025
**Statut** : ✅ Automatisation complète opérationnelle
**Action requise** : Mettre à jour l'URL RSS dans Spotify for Creators
