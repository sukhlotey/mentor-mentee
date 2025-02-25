## Mentor Mentee

#### Prerequisites

* Python 3.10+
* Node.js & npm (for frontend assets)
* Redis (for caching & queue management)
* MariaDB
* Frappe Framework 
* Bench CLI
* Education app
* Erpnext app

#### Steps

Create new site if not have existing site
```bash
bench new-site mentor-mentee.localhost
```
```bash
cd frappe-bench/apps
```

```bash
git clone https://github.com/sukhlotey/mentor-mentee.git
or
bench get-app mentor_mentee --branch main https://github.com/sukhlotey/mentor-mentee.git

```
```bash
cd ..
```
#### This app contains education and erpnext app

```bash

bench get-app erpnext 
bench get-app education

# Install them on the site
bench --site mentor-mentee.localhost install-app erpnext
bench --site mentor-mentee.localhost install-app education
bench --site mentor-mentee.localhost install-app mentor-mentee
```
```
bench build
bench start
```
