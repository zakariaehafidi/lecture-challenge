# 📚 Lecture Challenge

20 pages par jour, chacun. Si l'un de vous oublie, il reçoit à minuit (heure de Paris) un challenge drôle tiré au hasard parmi 308, par WhatsApp (ou par email en secours). Il se filme, envoie la vidéo à l'autre, et c'est l'autre qui valide sur le site.

## Contenu du dépôt

| Fichier | Rôle |
|---|---|
| `index.html` | Le site (ouvert sur vos téléphones) |
| `data/challenges.json` | Les 308 challenges (modifiables) |
| `data/state.json` | Les lectures et challenges enregistrés (ne pas modifier à la main sauf les prénoms) |
| `scripts/daily_check.py` | Le programme qui vérifie chaque nuit et envoie les messages |
| `.github/workflows/daily-check.yml` | Le réveil qui lance ce programme chaque nuit |

---

## Installation (environ 20 minutes, une seule fois)

### 1. Créer le dépôt

1. Crée un compte sur [github.com](https://github.com) si tu n'en as pas.
2. Clique sur **New repository**. Nom : `lecture-challenge`. Coche **Public** (obligatoire pour GitHub Pages gratuit). Clique **Create repository**.
3. Clique sur **uploading an existing file**, puis glisse **tout le contenu** du dossier dézippé (pas le dossier lui-même). Clique **Commit changes**.

⚠️ **Vérification importante** : le dossier `.github` est « caché » sur Mac et parfois sur Windows, il peut ne pas avoir été envoyé. Sur la page du dépôt, vérifie que tu vois un dossier `.github`. S'il manque :
**Add file → Create new file**, tape comme nom exactement `.github/workflows/daily-check.yml`, colle le contenu du fichier `daily-check.yml`, puis **Commit changes**.

### 2. Activer le site

1. Dans le dépôt : **Settings → Pages**.
2. **Source** : *Deploy from a branch*. **Branch** : `main`, dossier `/ (root)`. **Save**.
3. Après 1 à 2 minutes, l'adresse du site s'affiche en haut : `https://TON-PSEUDO.github.io/lecture-challenge/`

### 3. Autoriser l'écriture automatique

**Settings → Actions → General**, tout en bas dans *Workflow permissions* : coche **Read and write permissions**, puis **Save**.

### 4. Créer le jeton pour le site

C'est la « clé » qui permet au site d'enregistrer vos lectures.

1. Clique sur ta photo en haut à droite → **Settings → Developer settings → Personal access tokens → Fine-grained tokens → Generate new token**.
2. **Token name** : `lecture-challenge`. **Expiration** : la durée la plus longue proposée (note la date dans ton agenda pour le renouveler).
3. **Repository access** : *Only select repositories* → choisis `lecture-challenge`.
4. **Permissions → Repository permissions → Contents** : **Read and write**. (Ne touche à rien d'autre.)
5. **Generate token**, puis copie le jeton (il commence par `github_pat_`). Il ne sera plus jamais affiché.

### 5. WhatsApp (CallMeBot, gratuit)

**Chacun de vous deux** doit le faire sur son propre téléphone :

1. Va sur [callmebot.com](https://www.callmebot.com/blog/free-api-whatsapp-messages/) et suis les instructions : ajouter le numéro du bot dans tes contacts, puis lui envoyer le message d'autorisation indiqué.
2. Le bot te répond avec ton **apikey** (un nombre). Note-le.

Si le bot ne répond pas (ça arrive), pas grave : l'email prend le relais.

### 6. Email de secours (Gmail)

1. Sur le compte Gmail qui enverra les messages, active la **validation en deux étapes**.
2. Va sur [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords), crée un mot de passe d'application nommé `lecture-challenge` et copie les 16 lettres.

### 7. Enregistrer les secrets

Dans le dépôt : **Settings → Secrets and variables → Actions → New repository secret**. Crée ceux-ci (le nom doit être **exactement** celui-là) :

| Nom | Valeur | Exemple |
|---|---|---|
| `PHONE_P1` | Ton numéro, format international | `+33612345678` |
| `CALLMEBOT_KEY_P1` | Ton apikey CallMeBot | `1234567` |
| `EMAIL_P1` | Ton email | `toi@gmail.com` |
| `PHONE_P2` | Numéro d'Intissar | `+33698765432` |
| `CALLMEBOT_KEY_P2` | Apikey d'Intissar | `7654321` |
| `EMAIL_P2` | Email d'Intissar | `intissar@gmail.com` |
| `GMAIL_USER` | Le Gmail qui envoie | `toi@gmail.com` |
| `GMAIL_APP_PASSWORD` | Le mot de passe d'application (16 lettres) | `abcd efgh ijkl mnop` |

P1 = toi, P2 = Intissar.

### 8. Tester les messages

**Actions → Vérification quotidienne → Run workflow**, choisis `test-notifications`, puis **Run workflow**.
Vous devez recevoir tous les deux un message de test. Si la coche est rouge, clique dessus pour lire ce qui n'a pas marché (secret mal nommé, apikey erronée…).

### 9. Se connecter sur les téléphones

1. Ouvre l'adresse du site sur ton téléphone. Colle le jeton de l'étape 4, clique **Se connecter**, puis **C'est moi**.
2. Dans **Réglages**, mets ton vrai prénom et clique **Enregistrer les prénoms**.
3. Toujours dans **Réglages**, clique **Créer le lien d'invitation** puis **Envoyer par WhatsApp** à Intissar. Elle l'ouvre, et elle est connectée directement.
4. Astuce : dans le navigateur du téléphone, « Ajouter à l'écran d'accueil » pour l'avoir comme une appli.

C'est fini ! 🎉

---

## Comment ça marche au quotidien

- Chaque jour, avant minuit (heure de Paris), chacun clique **J'ai lu mes 20 pages**.
- Vers minuit et 5, GitHub vérifie. Celui qui n'a pas validé reçoit son challenge (sans répétition tant que les 308 n'ont pas été faits).
- Il se filme et envoie la vidéo à l'autre sur WhatsApp. L'autre clique **J'ai vu la vidéo : valider**. On ne peut pas valider son propre challenge.
- En cas de retard de GitHub, une vérification de rattrapage a lieu à 8 h.

## Modifier les challenges

Ouvre `data/challenges.json` sur GitHub, clique sur le crayon ✏️, modifie, puis **Commit changes**. Garde le format `{ "id": 309, "text": "..." }` et des numéros `id` tous différents.

## Bon à savoir

- **Sécurité** : le jeton n'est jamais enregistré dans le dépôt, seulement sur vos téléphones. Le lien d'invitation le contient : ne l'envoie qu'à Intissar. Si tu penses qu'il a fuité, supprime-le sur GitHub (étape 4) et crée-en un nouveau.
- **Dépôt public** : n'importe qui peut voir vos prénoms et vos jours de lecture dans `data/state.json`, mais **pas** vos numéros ni vos emails (ils sont dans les secrets).
- **Jeton expiré** : le site affiche « Le jeton GitHub est invalide ou a expiré ». Crée-en un nouveau (étape 4), puis **Réglages → Se déconnecter** et reconnecte-toi. Refais un lien d'invitation pour Intissar.
- **Pause de 60 jours** : GitHub désactive les vérifications automatiques d'un dépôt public sans activité depuis 60 jours. Tant que vous validez vos lectures, ça n'arrive pas. Sinon : **Actions → Vérification quotidienne → Enable workflow**.
- Le jour où vous commencez est le premier jour compté : aucun challenge pour les jours d'avant.
