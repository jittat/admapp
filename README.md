# คู่มืออย่างย่อ

หมายเหตุ: อ่านคู่มือเต็มได้ที่ wiki บน GitHub

## ติดตั้ง

หลังจากลง Django เรียบร้อยแล้ว จึงติดตั้ง requirement เพิ่มเติมของ project นี้ด้วย pip

    pip install -r requirements.txt

หลังจากนั้น นำเข้าข้อมูลเริ่มต้นใน fixtures

```
    ./manage.py migrate
    ./manage.py migrate --run-syncdb
    ./manage.py loaddata campuses faculties provinces admission_rounds
```


## ใช้ pipenv
สร้าง env และ install dependencies สำหรับทำครั้งแรก
```
    pipenv --python 3.8
    pipenv install
```
สำหรับเปิด shell เพื่อเข้าไปรันคำสั่ง manage.py ต่างๆ
```
    pipenv shell
```


## Dependencies
**ใช้ pipenv**  
ถ้าใช้ pipenv ระบบจะไปอ่าน dependencies version จาก Pipfile/Pipfile.lock  
requirements.txt จะไม่ถูกอ่าน ไม่มีผลเลย เวลาอัปเดต dependency ให้อัปใน Pipfile แล้วรันคำสั่งอัปเดต requirements.txt
```shell
pipenv requirements > requirements.txt
```
**ไม่ได้ใช้ pipenv**  
file requirements.txt จะถูกใช้อยู่ ก็ใช้ตามปกติ แต่ถ้าจะอัปเดต dependency ตัวไหน แนะนำให้ใช้ pipenv แล้วทำตามด้านบนจะดีกว่า


## MySql
ถ้าต้องการใช้ MySql สำหรับ develop สามารถรัน `docker-compose.yml` และตั้งค่า `/admapp/settings_local.py` เพิมเติมได้
```shell
docker-compose up
```

### Setup ครั้งแรก
1. เข้า phpMyAdmin http://localhost:8080/  
2. สร้าง database admapp
3. import database (ขอจากคนอื่น)
4. แก้ `/admapp/settings_local.py` ให้ใช้ mysql database
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'admapp',
        'USER': 'root',
        'PASSWORD': 'example',
        'HOST': '127.0.0.1',
        'PORT': '3306',
    }
}
```
