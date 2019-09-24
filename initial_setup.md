# Initial Setup
- **Make sure python3 is installed on the system.**

1. ```run.py```  setup:
     - When deploying, make sure that  ```debug``` is set to ```False```
     - To make the server publicly available add ```host='0.0.0.0'``` in ```app.run()```. To use a different port than 5000, for example port 80, add: ```port=80```
2. ```/avr/__init__.py```  setup: Change the correct settings for:
    - **MAIL_SERVER** - for example: ```smtp.googlemail.com```
    - **MAIL_PORT** - for example: ```587```
    - **MAIL_USE_TLS**  - ```True``` or ```False```
    - **RECAPTCHA_PUBLIC_KEY** - You need to get a pair of public and private keys from [Google reCAPTCHA](https://www.google.com/recaptcha/)
    
3. Environment variables setup:
    - **FLASK_SECRET_KEY** (flask uses this to keep the client-side sessions secure). You can generate your own using the python shell: ```import secrets``` and then ```secrets.token_hex(16)```
    - **EMAIL_USER**
    - **EMAIL_PASS**
    - **RECAPTCHA_PRIVATE_KEY**
4. Verify that a default profile picture named ```default.png``` exists in ```avr/static/images/profile/```
5. Install required packages:
    - In the main folder (where run.py exists) create a virtual environment named venv: ```python3 -m venv venv```
    - Active it:   
        In **Linux**: ```source venv/bin/activate```  
        In **Windows**: ```venv\Scripts\activate```
    - Install Wheel: ```pip install wheel```
    - Install all the packages the project uses: ```pip install -r requirements.txt```
6. Run the application using flask's built-in development server: ```python3 run.py```  
    This will also create the database file (in case it did not exist before).
7. Navigate to ```/CreateAdminAccount``` and create an admin accout (this page will not be accessible after creating an admin account)
8. Add at least one course in the ```Course``` table
9. Navigate to the supervisors page in the admin page and add some supervisors
10. Navigate to the proposed projects page in the admin page and add some proposed projects
11. Create a folder named "credentials" in avr\youtubeUpload\. After configuring OAuth 2.0 in the google api console, create a subfolder for each client (folder names must be sequential starting at "1", next client resides in folder named "2" and so on). in each client folder create a file named "client_secrets.json" with all the information from the API Console (can be downloaded from the google api console). (make sure its "client_secrets.json" and not "client_secret.json")
12. in "youtubeUpload/youtubeUpload.py" set the num_of_clients variable

### Enjoy :wink:
