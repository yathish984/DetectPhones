# DetectPhones
This is a simple Phone Detection Web Application built using FastAPI (Backend) and HTML + JavaScript (Frontend). It scans the local network and detects active devices (such as phones) connected to the Wi-Fi network.  The backend provides a REST API endpoint to return detected devices, and the frontend displays the result with a button click.
Great ✅
Here is your complete GitHub-ready README.md for this phone-detection project.

📱 Phone Detection System using FastAPI

This project detects nearby devices (phones/laptops) on a local network using Wi-Fi scanning and displays the results in a simple frontend UI.

The backend runs on FastAPI and exposes an API to scan and return connected devices.
The frontend uses HTML + JavaScript to call the API and show detected phones.

🚀 Features

Scan Wi-Fi network for connected devices

FastAPI backend

Lightweight, fast, easy to deploy

Simple web UI to trigger scans

Shows device count

🛠️ Tech Stack
Component	Technology
Backend	FastAPI (Python)
Frontend	HTML, JavaScript
Network Scan	Python ARP / Wi-Fi scan
Runner	Uvicorn
📂 Folder Structure
phone-detection/
│── main.py
│── wifi_scan.py
│── bt_scan.py (optional if you remove bluetooth)
│── vision_detect.py (optional if no vision)
│── static/
│   └── index.html
└── requirements.txt

▶️ How to Run
Install dependencies
pip install -r requirements.txt

Run FastAPI server
uvicorn main:app --reload

Open Browser

Visit:

http://127.0.0.1:8000


Click Scan → View detected devices.

📡 API Endpoint
Method	Endpoint	Description
GET	/scan	Returns detected devices
Example Response
{
  "device_count": 5,
  "devices": [
    "192.168.1.10",
    "192.168.1.11"
  ]
}

🧭 TODO / Future Enhancements

Show device names + MAC ID

Add Bluetooth device scanning

Add camera-based phone detection with YOLO

Admin dashboard + authentication

Store logs in database

📜 License

MIT License
Contact

For queries, contact: yathish984@gmail.com

📧 Contact

For queries, contact: your-email
