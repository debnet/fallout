# Déploiement natif avec Ansible

Ce playbook installe Fallout RPG **sans Docker** : PostgreSQL local, Redis dédié,
venv Python, Gunicorn et Celery sous systemd, Nginx public et certificat
Let's Encrypt. HTTP redirige vers HTTPS, sauf le challenge ACME. Le renouvellement
est vérifié deux fois par jour avec rechargement de Nginx après succès.

## Prérequis

- Contrôleur : Python et `ansible-core >= 2.19`, accès SSH et élévation sudo.
- Cible : distribution Debian-like ou RHEL-like **avec systemd**, Python système
  pour Ansible, et un Python applicatif **>= 3.13** capable de créer un venv.
  Debian 13 convient à cette contrainte ; ne pas supposer que toutes les versions
  Debian, Ubuntu ou RHEL fournissent déjà Python 3.13.
- PostgreSQL **>= 14**, Nginx, Redis et Certbot disponibles dans les dépôts
  configurés. Sur RHEL, Certbot peut nécessiter EPEL, à activer selon ta politique.
  Le playbook n'ajoute aucun dépôt tiers et ne met pas à niveau un cluster existant.
- Le domaine (A et, si publié, AAAA) pointe vers la cible. Les ports **80 et 443**
  doivent être accessibles depuis Internet, y compris pour les renouvellements.
  Le pare-feu/cloud security group reste sous ta responsabilité ; aucun pare-feu
  existant n'est remplacé ou désactivé.
- Préférer un serveur dédié. Les noms `fallout`, `fallout-redis`, la base `fallout`
  et `/etc/nginx/conf.d/fallout.conf` sont réservés à ce déploiement. Ne pas lancer
  deux playbooks simultanément sur le même serveur ou la même base.

La détection de famille choisit les paquets et l'initialisation PostgreSQL. Les
versions/interpréteurs/paquets atypiques restent configurables : voir
`vars.example.yml`. L'interpréteur `ansible_python_interpreter` doit pouvoir
importer le pilote PostgreSQL système ; `fallout_python` désigne le Python du venv,
qui peut être différent. Pour les paquets PGDG, adapter les noms de paquets,
service, répertoire de données et programme d'initialisation avant exécution.

## Configuration et lancement

Depuis la racine du dépôt, construire d'abord la wheel :

```bash
python -m build
python -m venv /path/to/ansible-venv
/path/to/ansible-venv/bin/pip install 'ansible-core>=2.19,<2.22'
source /path/to/ansible-venv/bin/activate
cd ansible
ansible-galaxy collection install -r requirements.yml
cp inventory.example.ini inventory.ini
cp vars.example.yml vars.yml
ansible-vault create vault.yml
```

Éditer l'inventaire et `vars.yml` (domaine, e-mail ACME, chemin de wheel et Python).
Les chemins relatifs de wheel sont relatifs au dossier `ansible/` dans cette
procédure. Utiliser un chemin absolu si les commandes sont lancées ailleurs.
Dans `vault.yml`, définir :

```yaml
fallout_secret_key: SECRET_ALEATOIRE_URLSAFE_AU_MOINS_50_CARACTERES
fallout_db_password: AUTRE_SECRET_ALEATOIRE_URLSAFE_AU_MOINS_32_CARACTERES
fallout_admin_password: MOT_DE_PASSE_INITIAL_FORT
```

Générer séparément les deux secrets techniques avec
`python -c 'import secrets; print(secrets.token_urlsafe(48))'`.
Ils sont limités à `A-Z a-z 0-9 _ -` pour une utilisation sûre dans le fichier
d'environnement et l'URL PostgreSQL. Le mot de passe admin n'a pas cette restriction,
mais doit satisfaire les validateurs de production Django.

```bash
ansible-playbook -i inventory.ini deploy.yml -e @vars.yml -e @vault.yml --ask-vault-pass --syntax-check
ansible-playbook -i inventory.ini deploy.yml -e @vars.yml -e @vault.yml --ask-vault-pass --ask-become-pass
```

Ne pas désactiver la vérification des clés SSH et ne pas placer les secrets dans
les arguments `-e secret=...`. Les fichiers locaux de configuration sont ignorés
par Git. Les tâches manipulant les secrets sont masquées et le diff du fichier
d'environnement est désactivé. Le mode `--check` ne simule pas un déploiement
complet (certificats, base et venv doivent réellement exister).

## Initialisation et mises à jour

Le playbook :

1. prépare les services locaux et une release identifiée par le hash de la wheel ;
2. obtient/conserve le certificat et installe la configuration HTTPS ;
3. arrête web et worker existants, puis réalise un `pg_dump` privé ;
4. lance migrations, `bootstrap`, `collectstatic` et contrôles Django ;
5. bascule le lien `current`, démarre les services, vérifie Gunicorn et HTTPS.

Il y a donc une **interruption de service pendant les mises à jour**, pas de
promesse de rolling deployment. Si l'initialisation échoue, le playbook s'arrête :
il ne redémarre pas aveuglément l'ancien code sur un schéma potentiellement modifié.
Les sorties de l'initialisation sont masquées pour protéger le secret initial.
Pour diagnostiquer, relancer les commandes nécessaires sous le compte `fallout`
avec `/etc/fallout/environment` chargé, sans exposer son contenu.

Sur une base neuve, `bootstrap` charge ensemble `admin`, `items` et `creatures` et
remplace le mot de passe admin avant commit. Dès qu'un utilisateur existe, aucun
réimport ni reset n'est effectué. Un catalogue sans utilisateur est refusé pour
ne pas l'écraser. Retirer `fallout_admin_password` du vault après le premier succès.
Il n'est jamais écrit dans l'environnement systemd, seulement transmis à
l'initialisation. Conserver les secrets Django et PostgreSQL entre déploiements.

## Exploitation et limites

- Code/venvs : `/opt/fallout/releases/`, lien `/opt/fallout/current`. Code détenu
  par root ; application et worker non-root, écriture limitée à l'instance.
- Instance : `/var/lib/fallout`, médias privés dans `medias/`, statiques publics
  dans `static/`. Nginx bloque `/medias/` : définir une livraison authentifiée
  séparée pour les uploads, sans exposer le dossier entier.
- Secrets : `/etc/fallout/environment`, root:fallout, `0640`.
- Redis dédié : `127.0.0.1:6380`, AOF dans `/var/lib/fallout-redis`, `noeviction`.
  La configuration Redis système éventuellement préexistante n'est pas modifiée.
- PostgreSQL utilise les réglages d'écoute de la distribution : vérifier qu'il
  reste local et filtré. Seule une règle SCRAM pour `fallout` sur loopback est
  ajoutée en tête du HBA ; les autres bases/règles ne sont pas remplacées.
- SELinux reste actif : labels des statiques/Redis et autorisation de connexion
  Nginx configurés lorsque SELinux est activé. Cela élargit la permission réseau
  des processus HTTP ; l'hôte doit rester de confiance.
- Pas de serveur Celery Beat : aucun planning périodique n'est défini actuellement.
  Worker JSON uniquement ; vider les anciennes tâches pickle avec l'ancien worker
  de confiance avant migration depuis une ancienne installation.

Commandes utiles :

```bash
sudo systemctl status fallout-web fallout-worker fallout-redis nginx fallout-certbot.timer
sudo journalctl -u fallout-web -u fallout-worker -f
sudo certbot renew --dry-run --cert-name rpg.example.org
```

Les dumps pré-migration sont dans `/var/backups/fallout/` (accès postgres seul).
Ils ne remplacent pas une stratégie de sauvegarde hors machine : sauvegarder aussi
les médias et secrets, définir une rétention et tester les restaurations.
Les anciennes releases ne sont pas supprimées automatiquement. Un retour de code
ne revient **pas** sur les migrations : décider explicitement du rollback et de
la restauration de base. Prévoir limites mémoire/CPU, rotation/rétention des
journaux, supervision du disque, de Redis, de Celery et des renouvellements TLS.

La wheel fixe la version applicative et Gunicorn est épinglé, mais les dépendances
transitives du venv ne sont pas verrouillées. Utiliser un index/wheelhouse contrôlé
pour une reproductibilité stricte. Les paquets OS suivent les dépôts de la cible.
Tester d'abord sur une VM de préproduction : la validation syntaxique ne remplace
pas un déploiement réel sur chaque distribution ciblée.

## Vérifications locales sans déploiement

```bash
ansible-playbook -i inventory.example.ini deploy.yml --syntax-check
ansible-playbook -i localhost, tests/render.yml
# Si ansible-lint est installé :
ansible-lint deploy.yml tls.yml redis-selinux.yml tests/render.yml
```

Le test de rendu ne modifie aucun service : il génère les templates dans un
répertoire temporaire, vérifie le script shell et les deux étapes HTTP/HTTPS,
puis retire uniquement son répertoire de test. Il ne contacte pas Let's Encrypt.
