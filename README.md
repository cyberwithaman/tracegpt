# TraceGPT 🚀

![Django](https://img.shields.io/badge/Django-092E20?style=for-the-badge&logo=django&logoColor=white)
![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Pandas](https://img.shields.io/badge/Pandas-2C2D72?style=for-the-badge&logo=pandas&logoColor=white)
![Matplotlib](https://img.shields.io/badge/Matplotlib-%23ffffff.svg?style=for-the-badge&logo=Matplotlib&logoColor=black)

**TraceGPT** is a Django application for debugging and analyzing AI chatbot traces with advanced visualization capabilities.

## ✨ Features

### 📊 Analytics Dashboard
- Runtime distribution histograms 📈
- Tag comparison radar charts 🎯
- Step type performance boxplots 📦
- Weekly activity heatmaps 🔥

### 🎨 Visualizations
- Interactive charts with Matplotlib and Seaborn 🖼️
- Timezone-aware datetime handling ⏰
- Performance metrics tracking 🏎️
- Tag distribution analysis 🏷️

### 🛠️ Admin Interface
- Modern UI with Jazzmin theme 💅
- Color-coded status badges 🟢🔴🟡🔵
- Custom chart views 📊
- Performance reports 📄

## 🚀 Getting Started

### Prerequisites
- Python 3.8+
- PostgreSQL (recommended) 🐘

### Installation
1. Clone the repository
```bash
git clone https://github.com/cyberwithaman/tracegpt.git
cd tracegpt
```

2. Create and activate virtual environment
```bash
python -m venv venv
venv\Scripts\activate
```

3. Install dependencies
```bash
pip install -r requirements.txt
```

4. Configure environment variables
Create a `.env` file:
```ini
SECRET_KEY=your-secret-key-here
DEBUG=True
DATABASE_URL=postgres://user:password@localhost:5432/tracegpt
```

5. Run migrations
```bash
python manage.py migrate
```

6. Create superuser
```bash
python manage.py createsuperuser
```

7. Run development server
```bash
python manage.py runserver
```

## 🏗️ Project Structure

```
tracegpt/
├── tracegptapp/          # Main Django app
│   ├── admin.py         # Admin configurations
│   ├── analytics.py     # Data processing and visualization
│   ├── models.py        # Database models
│   ├── urls.py          # App URLs
│   └── visualizations.py # Advanced chart generation
├── tracegpt/            # Project settings
├── static/              # Static files
├── templates/           # HTML templates
└── manage.py            # Django CLI
```

## 📈 Data Models

### Key Entities

| Model | Description |
|-------|-------------|
| `ChatTrace` | Records chatbot execution traces 🕵️ |
| `TraceStep` | Individual steps in a trace 👣 |
| `ChatExample` | Example conversations for testing 📝 |
| `ContactMessage` | User feedback messages 💬 |

## 🤝 Contributing

1. Fork the project
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 🙏 Acknowledgments

- Django for the awesome web framework
- Matplotlib/Seaborn for beautiful visualizations
- Pandas for powerful data analysis
- Jazzmin for the modern admin interface 

### 🔗 Connect with Me 
 
<p align="center">
  <a href="mailto:cyberwithaman@gmail.com"><img src="https://img.icons8.com/color/48/000000/gmail-new.png" alt="Email"/></a>
  <a href="tel:+917892939127"><img src="https://img.icons8.com/color/48/000000/phone.png" alt="Phone"/></a>
  <a href="https://www.instagram.com/cyberwithaman"><img src="https://img.icons8.com/color/48/000000/instagram-new.png" alt="Instagram"/></a>
  <a href="https://wa.me/+917892939127"><img src="https://img.icons8.com/color/48/000000/whatsapp--v1.png" alt="WhatsApp"/></a>
  <a href="https://github.com/cyberwithaman"><img src="https://img.icons8.com/ios-filled/48/ffffff/github.png" style="background-color:#181717; border-radius:50%; padding:6px;" alt="GitHub"/></a>
  <a href="https://www.linkedin.com/in/cyberwithaman"><img src="https://img.icons8.com/color/48/000000/linkedin.png" alt="LinkedIn"/></a>
</p>