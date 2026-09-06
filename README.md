# 🌍 Smart Safar

Smart Safar is a **travel planning web application** built with **Python and Flask**. It helps users explore destinations and provides useful travel information such as **weather, air quality, hotels, locations, and routes** using various APIs.

The project is designed to bring multiple travel-related services together in one simple platform.

## ✨ Features

* 🌍 Explore travel destinations
* 🌤️ Check weather information
* 🌫️ Check air quality
* 🏨 Search for hotels
* 📍 Location and place information
* 🛣️ Route and navigation support
* 🔌 Integration with multiple travel APIs

## 🛠️ Tech Stack

* **Backend:** Python, Flask
* **Frontend:** HTML, CSS, JavaScript, Jinja2
* **APIs:** Weather API, IQAir, Geoapify, OpenRouteService, Hotel API
* **Libraries:** Requests, Pytrends

## 🚀 How to Run

### 1. Clone the repository

```bash
git clone https://github.com/rishabh-o36/Smart-Safar.git
cd Smart-Safar/m4lko
```

### 2. Create a virtual environment

**Windows:**

```bash
python -m venv venv
venv\Scripts\activate
```

**macOS/Linux:**

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Add API Keys

Create a `.env` file and add the required API keys:

```env
WEATHER_API_KEY=your_key
IQAIR_API_KEY=your_key
GEOAPIFY_API_KEY=your_key
HOTEL_API_KEY=your_key
ORS_API_KEY=your_key
FLASK_SECRET_KEY=your_secret_key
```

> **Note:** Never commit your API keys or `.env` file to GitHub.

### 5. Run the application

```bash
python app.py
```

Open your browser and visit:

```text
http://127.0.0.1:5000
```

## 👨‍💻 Author

**Rishabh**

GitHub: https://github.com/rishabh-o36
