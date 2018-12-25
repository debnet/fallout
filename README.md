# Fallout RPG

This project aims to provide tools to a Fallout RPG (or Pen & Paper) gamemaster.

The game system is **not** a copy of the Fallout PnP by J. Sawyer, I changed many things 
I found very odd and which can broke the gameplay and/or the immersion. 
View this as my own and personal interpretation of the Fallout game system.

By the way, I'm still working of this system and I don't really care about the
retro-compatibility with existing or running projects (especially with database migrations),
so don't be surprised if a newer versions does not work above an older one.

Currenty the project includes:

* Campaigns
  * Time management
  * Loot management
  * Global effects
  * Radiation level
  * Turn sequence
* Characters and creatures
  * Primary and derived statistics
  * Health and actions
  * Single, targetted ou burst attacks
  * Damage management
  * Inventory and equipment management
  * Effects (malus, bonus, perks, traits)
  * S.P.E.C.I.A.L. and skills rolls
  * Rolls and fight history
* Items management (weapons, armors, consumables)
* Random loots

## How to use it?

#### With docker

This project is Docker-ready if you already have Compose. Just type this command line:

`docker-compose up --build`

It provides a local instance listening in `http://127.0.0.1:8000` 
with PostgreSQL and Redis as service.

By default, the administrator account is `admin` with password `admin`.

#### From Python

Like any Django project, you can start a development webserver with this command line:

`python manage.py runserver`

You have to install the requirements first with: `pip install -r requirements.txt`.
Don't hesitate to install them in a dedicated virtualenv.

## Any questions?

Feel free to provide any feedback or anomalies through an issue or an email.

There is no licence provided but you can fork, edit and redistribute the source code,
just keep me in touch because I'm curious of what the others do with my job. ;)
