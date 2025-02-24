## Mentor Mentee

#### Prerequisites

* Python 3.10+
* Node.js & npm (for frontend assets)
* Redis (for caching & queue management)
* MariaDB 10.3+ / MySQL
* Frappe Framework (v14 recommended)
* Bench CLI

#### Steps

```bash
bench new-site mentor-mentee.localhost
```
```bash
cd apps
```

```bash
git clone https://github.com/YOUR_GITHUB_USERNAME/mentor-mentee.git
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
bench start
```

